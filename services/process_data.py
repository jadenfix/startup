#services/process_data.py
 import json
 import os

 def process_order_data(raw_data_path, processed_data_path):
      try:
      # Create directories if they don't exist
         os.makedirs(os.path.dirname(processed_data_path), exist_ok=True)

         with open(raw_data_path, 'r') as file:
            orders = json.load(file)

         processed_orders = []
         for order in orders:
          processed_order = {
            "order_id": order["id"],
           "customer_id": order["customer_id"],
           "restaurant_id": order["restaurant_id"],
          "order_status": order["order_status"],
           "region": order["region"],
            "order_time": order["order_time"],
            "customer_lat": order["customer_lat"],
             "customer_lng": order["customer_lng"],
             "restaurant_lat": order["restaurant_lat"],
             "restaurant_lng": order["restaurant_lng"]

            }
         processed_orders.append(processed_order)

        with open(processed_data_path, 'w') as file:
         json.dump(processed_orders, file, indent=4)

         print(f"Processed order data written to: {processed_data_path}")
      except FileNotFoundError:
         print(f"Error: File not found at {raw_data_path}")
      except Exception as e:
          print(f"Error processing order data: {e}")
