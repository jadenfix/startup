"""Assign the nearest available driver to an order in its region."""
from db.models import Driver, Order
from sqlalchemy.orm import Session
from geopy.distance import geodesic


def assign_driver(session: Session, order_id: int, restaurant_location: tuple):
    order = session.query(Order).filter(Order.id == order_id).first()
    if order is None:
        return None
    if order.driver_id is not None:
        return session.query(Driver).filter(Driver.id == order.driver_id).first()
    query = session.query(Driver).filter(Driver.is_available == True)
    if order.region:
        query = query.filter(Driver.region == order.region)
    drivers = query.all()
    if not drivers:
        return None
    driver = min(drivers, key=lambda item: (geodesic((item.lat, item.lng), restaurant_location).miles, item.id))
    driver.is_available = False
    order.driver_id = driver.id
    session.commit()
    return driver
