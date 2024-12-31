    # `services/data_pipeline.py`
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    from datetime import datetime
    from services.process_data import process_order_data
    from services.analytics import predict_demand, preprocess_data, train_prophet_model
    from db.connection import SessionLocal
    from db.models import Order, Customer, Restaurant, Driver
    import logging
    import json
    import os


    RAW_DATA_PATH = "/tmp/data_pipeline/orders.json" # Can modify to be more dynamic
    PROCESSED_DATA_PATH = "/tmp/data_pipeline/processed_orders"
    logger = logging.getLogger('backend_logger')

    with DAG(
      dag_id="data_pipeline",
      start_date=datetime(2023, 1, 1),
      schedule_interval="@hourly",
       catchup=False,
     ) as dag:
         ingest_data = PythonOperator(
             task_id="ingest_order_data",
            python_callable=lambda: load_from_json_data(RAW_DATA_PATH),
         )
         process_data = PythonOperator(
              task_id="process_order_data",
              python_callable=lambda: process_order_data(RAW_DATA_PATH, PROCESSED_DATA_PATH),
           )
         generate_demand_forecast = PythonOperator(
               task_id="generate_demand_forecast",
                python_callable=lambda: generate_demand_forecast_data(PROCESSED_DATA_PATH)
           )

         ingest_data >> process_data >> generate_demand_forecast
    def load_from_json_data(filepath):

      try:
          session = SessionLocal()
           # Load data from files and insert into DB.

          if not os.path.exists(filepath):
           raise FileNotFoundError(f"Could not load filepath {filepath}")

          with open(filepath, 'r') as file:
              orders = json.load(file)
          for order_data in orders:
           customer = session.query(Customer).filter(Customer.id == order_data['customer_id']).first()
           restaurant = session.query(Restaurant).filter(Restaurant.id == order_data['restaurant_id']).first()
           if not customer or not restaurant:
              continue # skip inserting order for customers/restaurants that do not exist

           order = Order(**order_data)
           session.add(order)
          session.commit()
          logger.info('Data loaded to DB via airflow successfully')
      except FileNotFoundError as e:
        logger.error(f"File not found : {e}")
      except Exception as e:
           logger.error(f"Error when inserting to database : {e}")
      finally:
         session.close()

    def generate_demand_forecast_data(processed_data_path):
        session = SessionLocal()
        orders = session.query(Order).all()
        order_history = []
        for order in orders:
           order_history.append(
            {"order_id": order.id,
              "order_time": order.order_time,
           })

        df = preprocess_data(order_history=order_history)
        if df is not None:
            model = train_prophet_model(df=df)
            if model is not None:
              forecast = predict_demand(model, df)
              logger.info(f"Forecast : {forecast.tail()}")
            else:
              logger.error('Could not train model')
        else:
             logger.error('Could not preprocess the data')
        session.close()