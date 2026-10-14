"""Local delivery API; deployment authentication requires a gateway."""
import math
from flask import Flask, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest, UnsupportedMediaType
from db.connection import SessionLocal, init_db
from db.models import Order
from services.driver_matching import assign_driver
from services.order_management import create_order, update_order_status
from services.pricing import calculate_delivery_fee


def create_app(session_factory=SessionLocal):
    app = Flask(__name__)

    @app.errorhandler(ValueError)
    @app.errorhandler(BadRequest)
    @app.errorhandler(UnsupportedMediaType)
    def invalid_request(error):
        return jsonify(error=str(error)), 400

    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        app.logger.exception("Database operation failed")
        return jsonify(error="Database operation failed"), 500

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.post("/orders")
    def create_new_order():
        data = request.get_json()
        if not isinstance(data, dict):
            raise ValueError("Expected a JSON object")
        for key in ("customer_id", "restaurant_id"):
            if type(data.get(key)) is not int or data[key] < 1:
                raise ValueError(f"{key} must be a positive integer")
        with session_factory() as session:
            order = create_order(session, data["customer_id"], data["restaurant_id"])
            return jsonify(order_id=order.id, message="Order created successfully"), 201

    @app.get("/orders/<int:order_id>")
    def get_order(order_id):
        with session_factory() as session:
            order = session.get(Order, order_id)
            if order is None:
                return jsonify(error="Order does not exist"), 404
            return jsonify(order_id=order.id, customer_id=order.customer_id,
                           restaurant_id=order.restaurant_id, driver_id=order.driver_id,
                           status=order.order_status, region=order.region)

    # Retain GET for existing clients; new clients should use POST.
    @app.patch("/orders/<int:order_id>/status")
    def change_status(order_id):
        data = request.get_json()
        if not isinstance(data, dict) or data.get("status") not in {"delivered", "cancelled"}:
            raise ValueError("status must be delivered or cancelled")
        with session_factory() as session:
            order = update_order_status(session, order_id, data["status"])
            if order is None:
                return jsonify(error="Order does not exist"), 404
            return jsonify(order_id=order.id, status=order.order_status)

    @app.route("/drivers/assign/<int:order_id>", methods=["POST", "GET"])
    def assign_driver_route(order_id):
        with session_factory() as session:
            order = session.get(Order, order_id)
            if order is None:
                return jsonify(error="Order does not exist"), 404
            driver = assign_driver(session, order_id)
            if driver is None:
                return jsonify(error="No driver available"), 409
            return jsonify(driver_id=driver.id, driver_region=driver.region,
                           message=f"Driver assigned: {driver.name}")

    @app.post("/pricing")
    def calculate_price():
        data = request.get_json()
        if not isinstance(data, dict):
            raise ValueError("Expected a JSON object")
        locations = []
        for key in ("customer_location", "restaurant_location"):
            value = data.get(key)
            if not isinstance(value, list) or len(value) != 2:
                raise ValueError(f"{key} must contain latitude and longitude")
            if any(type(v) not in (int, float) or not math.isfinite(v) for v in value):
                raise ValueError(f"{key} coordinates must be finite numbers")
            if not (-90 <= value[0] <= 90 and -180 <= value[1] <= 180):
                raise ValueError(f"{key} coordinates are out of range")
            locations.append(tuple(value))
        return jsonify(delivery_fee=calculate_delivery_fee(*locations))

    return app


app = create_app()

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000)
