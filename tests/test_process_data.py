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
