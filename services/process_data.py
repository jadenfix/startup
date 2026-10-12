"""Normalize every raw order into a JSON batch for downstream processing."""
import json
from pathlib import Path


def process_order_data(raw_data_path, processed_data_path):
    with open(raw_data_path, encoding="utf-8") as source:
        orders = json.load(source)
    fields = ("customer_id", "restaurant_id", "order_status", "region",
              "order_time", "customer_lat", "customer_lng", "restaurant_lat", "restaurant_lng")
    processed = [{"order_id": order["id"], **{key: order[key] for key in fields}}
                 for order in orders]
    destination = Path(processed_data_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(processed, indent=4), encoding="utf-8")
