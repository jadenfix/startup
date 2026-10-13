# api/api_routes.py
from flask import Flask, request, jsonify
from services.order_management import create_order
from services.driver_matching import assign_driver
from services.pricing import calculate_delivery_fee
from db.connection import SessionLocal
from config.config import config
from db.models import Restaurant, Customer, Order
import json

app = Flask(__name__)

@app.route('/orders', methods=['POST'])
def create_new_order():
    try:
        data = request.get_json()
        if not data or 'customer_id' not in data or 'restaurant_id' not in data:
            return jsonify({'error': 'Missing order data or invalid json body'})
        session = SessionLocal()
        order = create_order(session=session, customer_id=data['customer_id'], restaurant_id=data['restaurant_id'])
        return jsonify({'order_id': order.id, 'message': 'Order created successfully'}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/drivers/assign/<int:order_id>', methods=['GET'])
def assign_driver_route(order_id):
    try:
        session = SessionLocal()
        order = session.query(Order).filter(Order.id == order_id).first()
        if not order:
            return jsonify({'error': 'Order does not exist'}), 404
        restaurant = session.query(Restaurant).filter(Restaurant.id == order.restaurant_id).first()
        restaurant_location = (restaurant.lat, restaurant.lng)
        driver = assign_driver(session=session, order_id=order_id, restaurant_location=restaurant_location)
        if not driver:
            return jsonify({'message': 'Could not assign a driver at the moment'}), 404
        return jsonify({'driver_id': driver.id, 'message': f'Driver assigned: {driver.name}'}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/pricing', methods=['POST'])
def calculate_price():
    try:
        data = request.get_json()
        if not data or 'customer_location' not in data or 'restaurant_location' not in data:
            return jsonify({'error': 'Customer or Restaurant location missing'})

        customer_location = tuple(data['customer_location'])
        restaurant_location = tuple(data['restaurant_location'])
        fee = calculate_delivery_fee(customer_location=customer_location, restaurant_location=restaurant_location)

        return jsonify({'delivery_fee': fee})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    config.load_env()
    app.run(debug=True, port=5000)