# tests/test_services.py
import unittest
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base, Customer, Driver, Restaurant, Order
from services.order_management import create_order
from services.driver_matching import assign_driver
from services.pricing import calculate_delivery_fee
from services.routing import get_optimized_route
from services.demand_prediction import (preprocess_data, train_prophet_model, predict_demand)
from config.config import config

# Use a test database in memory for testing
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_session():
   test_session = TestingSessionLocal()
   yield test_session
   test_session.close()
def mock_get_request(*args, **kwargs):
       class MockResponse:
          def __init__(self, json_data, status_code):
             self.json_data = json_data
             self.status_code = status_code
          def json(self):
             return self.json_data
          def raise_for_status(self):
              if self.status_code != 200:
                  raise Exception()

       return MockResponse({"routes":[]}, 200)


class TestServices(unittest.TestCase):
    def setUp(self):
         Base.metadata.drop_all(bind=engine)
         Base.metadata.create_all(bind=engine)
         # Set up test data in in-memory test database
         self.session = TestingSessionLocal()

         customer = Customer(name="Test Customer", lat=37.7749, lng=-122.4194, region='Region_A', address="address 1")
         restaurant = Restaurant(name="Test Restaurant", lat=37.7849, lng=-122.4094, region='Region_A',address="address 2", cuisine='italian')
         driver = Driver(name="Test Driver", lat=37.7949, lng=-122.3994, region='Region_A', address="address 3", is_available=True)
         driver_not_available = Driver(name="Test Driver", lat=37.7949, lng=-122.3994, region='Region_A', address="address 3", is_available=False)

         self.session.add(customer)
         self.session.add(restaurant)
         self.session.add(driver)
         self.session.add(driver_not_available)
         self.session.commit()
         self.customer_id = customer.id
         self.restaurant_id = restaurant.id
         self.driver_id = driver.id

    def tearDown(self):
          # Clean up the database
           self.session.close()

    def test_create_order(self):
         order = create_order(session=self.session, customer_id=self.customer_id, restaurant_id=self.restaurant_id)
         self.assertIsNotNone(order.id)
         retrieved_order = self.session.query(Order).filter(Order.id==order.id).first()
         self.assertEqual(retrieved_order.customer_id, self.customer_id)
         self.assertEqual(retrieved_order.restaurant_id, self.restaurant_id)


    def test_assign_driver_success(self):
       order = create_order(session=self.session, customer_id=self.customer_id, restaurant_id=self.restaurant_id)
       restaurant = self.session.query(Restaurant).filter(Restaurant.id==self.restaurant_id).first()
       restaurant_location = (restaurant.lat, restaurant.lng)
       driver = assign_driver(session=self.session, order_id=order.id, restaurant_location=restaurant_location)
       self.assertIsNotNone(driver)
       self.assertFalse(driver.is_available)

    def test_assign_driver_no_drivers_available(self):
      #set the only driver to false
      driver = self.session.query(Driver).filter(Driver.id==self.driver_id).first()
      driver.is_available = False
      self.session.commit()
      order = create_order(session=self.session, customer_id=self.customer_id, restaurant_id=self.restaurant_id)
      restaurant = self.session.query(Restaurant).filter(Restaurant.id==self.restaurant_id).first()
      restaurant_location = (restaurant.lat, restaurant.lng)
      driver = assign_driver(session=self.session, order_id=order.id, restaurant_location=restaurant_location)
      self.assertIsNone(driver)

    def test_calculate_delivery_fee(self):
      customer_location = (37.7749, -122.4194)
      restaurant_location = (37.7849, -122.4094)
      fee = calculate_delivery_fee(customer_location, restaurant_location)
      self.assertGreater(fee, 0)


    @patch('services.routing.requests.get', side_effect=mock_get_request)
    def test_get_optimized_route(self, mock_get):
         api_key="test-key"
         origin = "test origin"
         destination = "test destination"
         waypoints = ["waypoint1", "waypoint2"]
         routes = get_optimized_route(api_key=api_key, origin=origin, destination=destination, waypoints=waypoints)
         self.assertIsNotNone(routes)


    def test_preprocess_data(self):
         order_history = [
            { "order_id":1, "order_time": "2023-10-26T12:00:00"},
            { "order_id":2, "order_time": "2023-10-26T13:00:00"}
        ]
         df = preprocess_data(order_history)
         self.assertIsNotNone(df)
         self.assertIn("ds", df.columns)
         self.assertIn("y", df.columns)


    def test_train_prophet_model(self):
         order_history = [
           { "order_id":1, "order_time": "2023-10-26T12:00:00"},
             { "order_id":2, "order_time": "2023-10-26T13:00:00"}
        ]
         df = preprocess_data(order_history)
         model = train_prophet_model(df)
         self.assertIsNotNone(model)
    def test_predict_demand(self):
       order_history = [
           { "order_id":1, "order_time": "2023-10-26T12:00:00"},
           { "order_id":2, "order_time": "2023-10-26T13:00:00"}
        ]
       df = preprocess_data(order_history)
       model = train_prophet_model(df)
       forecast = predict_demand(model, df)
       self.assertIsNotNone(forecast)


if __name__ == '__main__':
    unittest.main()
