"""Optional Airflow pipeline; failed ingestion/processing/forecasting fails the task."""
import json
import os
from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator

from db.connection import SessionLocal
from db.models import Customer, Order, Restaurant
from services.demand_prediction import predict_demand, preprocess_data, train_prophet_model
from services.process_data import process_order_data

RAW_DATA_PATH = os.getenv("RAW_DATA_PATH", "/tmp/data_pipeline/orders.json")
PROCESSED_DATA_PATH = os.getenv("PROCESSED_DATA_PATH", "/tmp/data_pipeline/processed_orders.json")


def load_from_json_data(filepath):
    rows = json.loads(Path(filepath).read_text())
    if not isinstance(rows, list):
        raise ValueError("Expected a list of exported orders")
    with SessionLocal.begin() as session:
        for row in rows:
            if session.get(Customer, row["customer_id"]) is None or session.get(Restaurant, row["restaurant_id"]) is None:
                raise ValueError("Exported order references a missing customer or restaurant")
            if "id" in row and session.get(Order, row["id"]) is not None:
                continue  # Retried ingestion must not duplicate an existing exported order.
            values = dict(row)
            if isinstance(values.get("order_time"), str):
                values["order_time"] = datetime.fromisoformat(values["order_time"].replace("Z", "+00:00")).replace(tzinfo=None)
            session.add(Order(**values))


def generate_demand_forecast_data(processed_data_path):
    history = json.loads(Path(processed_data_path).read_text())
    data = preprocess_data(history)
    forecast = predict_demand(train_prophet_model(data), data)
    output = Path(processed_data_path).with_suffix(".forecast.json")
    output.write_text(forecast[["ds", "yhat"]].to_json(orient="records", date_format="iso"))
    return str(output)


with DAG(dag_id="data_pipeline", start_date=datetime(2023, 1, 1),
         schedule_interval="@hourly", catchup=False) as dag:
    ingest = PythonOperator(task_id="ingest_order_data", python_callable=load_from_json_data,
                            op_args=[RAW_DATA_PATH])
    process = PythonOperator(task_id="process_order_data", python_callable=process_order_data,
                             op_args=[RAW_DATA_PATH, PROCESSED_DATA_PATH])
    forecast = PythonOperator(task_id="generate_demand_forecast", python_callable=generate_demand_forecast_data,
                              op_args=[PROCESSED_DATA_PATH])
    ingest >> process >> forecast
