import json
from services.process_data import process_order_data


def test_process_keeps_every_order_and_creates_parent(tmp_path):
    fields = {"customer_id": 1, "restaurant_id": 2, "order_status": "pending",
              "region": "A", "order_time": "2026-10-12T12:00:00",
              "customer_lat": 37.0, "customer_lng": -122.0,
              "restaurant_lat": 37.1, "restaurant_lng": -122.1}
    raw = tmp_path / "raw.json"
    raw.write_text(json.dumps([{**fields, "id": 1}, {**fields, "id": 2}]))
    output = tmp_path / "nested" / "orders.json"
    process_order_data(raw, output)
    assert json.loads(output.read_text()) == [{**fields, "order_id": 1}, {**fields, "order_id": 2}]


def test_process_empty_batch(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    raw = tmp_path / "raw.json"
    raw.write_text("[]")
    process_order_data(raw, "output.json")
    assert json.loads((tmp_path / "output.json").read_text()) == []


def test_demand_uses_hourly_counts_instead_of_order_identifiers():
    from services.demand_prediction import preprocess_data
    result = preprocess_data([
        {"order_id": 100, "order_time": "2026-10-12T12:10:00"},
        {"order_id": 900, "order_time": "2026-10-12T12:40:00"},
        {"order_id": 2000, "order_time": "2026-10-12T14:00:00"},
    ])
    assert result["y"].tolist() == [2, 0, 1]


def test_http_order_assignment_and_pricing_workflow(monkeypatch):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from db.models import Base, Customer, Restaurant, Driver, Order
    from api import api_routes
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add_all([
        Customer(name="C", lat=37.0, lng=-122.0, region="A"),
        Restaurant(name="R", lat=37.1, lng=-122.1, region="A"),
        Driver(name="D", lat=37.11, lng=-122.11, region="A", is_available=True),
    ])
    session.commit()
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with api_routes.create_app(factory).test_client() as client:
        created = client.post("/orders", json={"customer_id": 1, "restaurant_id": 1})
        assert created.status_code == 201
        order_id = created.get_json()["order_id"]
        assigned = client.get(f"/drivers/assign/{order_id}")
        assert assigned.status_code == 200
        assert session.get(Order, order_id).driver_id == assigned.get_json()["driver_id"]
        assert client.get(f"/drivers/assign/{order_id}").get_json() == assigned.get_json()
        price = client.post("/pricing", json={"customer_location": [37.0, -122.0], "restaurant_location": [37.1, -122.1]})
        assert price.status_code == 200
        assert price.get_json()["delivery_fee"] > 0
        assert client.get("/drivers/assign/999999").status_code == 404
    session.close()
    engine.dispose()
