import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.api_routes import create_app
from db.models import Base, Customer, Driver, Order, Restaurant
from services.demand_prediction import preprocess_data
from services.driver_matching import assign_driver
from services.process_data import process_order_data


@pytest.fixture
def store(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'delivery.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        session.add_all([
            Customer(id=1, name="Jaden", lat=37.77, lng=-122.42, region="SF"),
            Restaurant(id=1, name="North Beach Kitchen", lat=37.80, lng=-122.41, region="SF"),
            Driver(id=1, name="Near", lat=37.801, lng=-122.410, region="SF"),
            Driver(id=2, name="Far", lat=37.75, lng=-122.45, region="SF"),
            Driver(id=3, name="Cross-region closer", lat=37.8001, lng=-122.4101,
                   region="OAK"),
        ])
        session.commit()
    yield factory
    engine.dispose()


def test_full_http_workflow_persists_assignment_and_repeat_is_idempotent(store):
    client = create_app(store).test_client()
    assert client.get("/health").json == {"status": "ok"}
    response = client.post("/orders", json={"customer_id": 1, "restaurant_id": 1})
    assert response.status_code == 201
    order_id = response.json["order_id"]
    response = client.post(f"/drivers/assign/{order_id}")
    assert response.status_code == 200
    assert response.json["driver_id"] == 1
    assert response.json["driver_region"] == "SF"
    assert client.post(f"/drivers/assign/{order_id}").json["driver_id"] == 1
    reopened = create_app(store).test_client()
    assert reopened.get(f"/orders/{order_id}").json["status"] == "assigned"
    with store() as session:
        assert session.get(Order, order_id).driver_id == 1
        assert session.get(Driver, 1).is_available is False
        assert session.get(Driver, 2).is_available is True
        assert session.get(Driver, 3).is_available is True


def test_assignment_uses_immutable_order_region_and_restaurant_location(store):
    client = create_app(store).test_client()
    oid = client.post("/orders", json={"customer_id": 1, "restaurant_id": 1}).json["order_id"]
    with store() as session:
        restaurant = session.get(Restaurant, 1)
        restaurant.region = "OAK"
        restaurant.lat = 37.75
        restaurant.lng = -122.45
        session.commit()

    response = client.post(f"/drivers/assign/{oid}")
    assert response.status_code == 200
    assert response.json["driver_id"] == 1
    assert response.json["driver_region"] == "SF"
    assert client.get(f"/orders/{oid}").json["region"] == "SF"
    with store() as session:
        assert session.get(Driver, 3).is_available is True


def test_out_of_region_capacity_is_not_used(store):
    with store() as session:
        session.get(Driver, 1).is_available = False
        session.get(Driver, 2).is_available = False
        session.commit()
    client = create_app(store).test_client()
    oid = client.post("/orders", json={"customer_id": 1, "restaurant_id": 1}).json["order_id"]
    response = client.post(f"/drivers/assign/{oid}")
    assert response.status_code == 409
    assert response.json == {"error": "No driver available"}
    with store() as session:
        assert session.get(Driver, 3).is_available is True


@pytest.mark.parametrize("payload", [None, [], {}, {"customer_id": True, "restaurant_id": 1},
                                      {"customer_id": "1", "restaurant_id": 1},
                                      {"customer_id": 1, "restaurant_id": 999}])
def test_invalid_order_does_not_write(store, payload):
    response = create_app(store).test_client().post("/orders", json=payload)
    assert response.status_code == 400
    with store() as session:
        assert session.query(Order).count() == 0


def test_no_capacity_returns_conflict_without_double_booking(store):
    client = create_app(store).test_client()
    for _ in range(2):
        oid = client.post("/orders", json={"customer_id": 1, "restaurant_id": 1}).json["order_id"]
        assert client.post(f"/drivers/assign/{oid}").status_code == 200
    oid = client.post("/orders", json={"customer_id": 1, "restaurant_id": 1}).json["order_id"]
    assert client.post(f"/drivers/assign/{oid}").status_code == 409
    assert client.get(f"/orders/{oid}").json["driver_id"] is None
    assert client.post("/drivers/assign/999").status_code == 404


def test_concurrent_assignments_do_not_double_book(store):
    with store() as session:
        session.get(Driver, 2).is_available = False
        session.add_all([Order(id=1, customer_id=1, restaurant_id=1),
                         Order(id=2, customer_id=1, restaurant_id=1)])
        session.commit()
    def assign(oid):
        with store() as session:
            driver = assign_driver(session, oid, (37.80, -122.41))
            return driver.id if driver else None
    with ThreadPoolExecutor(max_workers=2) as pool:
        assigned = list(pool.map(assign, [1, 2]))
    assert assigned.count(1) == 1
    assert assigned.count(None) == 1
    with store() as session:
        assert session.query(Order).filter(Order.driver_id == 1).count() == 1


def test_delivery_completes_and_releases_driver_without_reopening_order(store):
    client = create_app(store).test_client()
    oid = client.post("/orders", json={"customer_id": 1, "restaurant_id": 1}).json["order_id"]
    assert client.post(f"/drivers/assign/{oid}").json["driver_id"] == 1
    assert client.patch(f"/orders/{oid}/status", json={"status": "delivered"}).status_code == 200
    assert client.patch(f"/orders/{oid}/status", json={"status": "delivered"}).status_code == 200
    assert client.patch(f"/orders/{oid}/status", json={"status": "cancelled"}).status_code == 400
    assert client.post(f"/drivers/assign/{oid}").status_code == 400
    with store() as session:
        assert session.get(Driver, 1).is_available is True
        assert session.get(Order, oid).order_status == "delivered"


def test_cancelled_pending_order_never_reserves_a_driver(store):
    client = create_app(store).test_client()
    oid = client.post("/orders", json={"customer_id": 1, "restaurant_id": 1}).json["order_id"]
    assert client.patch(f"/orders/{oid}/status", json={"status": "cancelled"}).status_code == 200
    assert client.post(f"/drivers/assign/{oid}").status_code == 400
    with store() as session:
        assert session.get(Driver, 1).is_available is True


def test_pipeline_preserves_all_orders_and_relative_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    raw = tmp_path / "orders.json"
    raw.write_text(json.dumps([{"id": 101}, {"id": 999}]))
    process_order_data(raw, "processed.json")
    assert [r["order_id"] for r in json.loads((tmp_path / "processed.json").read_text())] == [101, 999]


def test_demand_counts_orders_instead_of_database_ids():
    result = preprocess_data([
        {"order_id": 100, "order_time": "2026-10-12T10:05:00Z"},
        {"order_id": 999, "order_time": "2026-10-12T10:15:00Z"},
        {"order_id": 5000, "order_time": "2026-10-12T12:15:00Z"},
    ])
    assert result.y.tolist() == [2, 0, 1]
    assert result.ds.dt.tz is None


@pytest.mark.parametrize("coordinates", [[91, 0], [0], [True, 0], [float("nan"), 0], [0, 181]])
def test_invalid_coordinates_are_rejected(store, coordinates):
    response = create_app(store).test_client().post("/pricing", json={
        "customer_location": coordinates, "restaurant_location": [0, 0]})
    assert response.status_code == 400
