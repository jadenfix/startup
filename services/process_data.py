"""Normalize every exported order, propagating failures to the pipeline."""
import json
from pathlib import Path


def process_order_data(raw_data_path, processed_data_path):
    orders = json.loads(Path(raw_data_path).read_text())
    if not isinstance(orders, list):
        raise ValueError("Expected a JSON list of orders")
    fields = ("customer_id", "restaurant_id", "order_status", "region", "order_time",
              "customer_lat", "customer_lng", "restaurant_lat", "restaurant_lng")
    processed = [{"order_id": order["id"], **{f: order.get(f) for f in fields}} for order in orders]
    output = Path(processed_data_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(processed, indent=2))
    return processed
