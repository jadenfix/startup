"""Persist nearest-driver reservations atomically."""
from geopy.distance import geodesic
from sqlalchemy import update
from sqlalchemy.orm import Session
from db.models import Driver, Order, Restaurant


def assign_driver(session: Session, order_id: int, restaurant_location: tuple | None = None):
    """Reserve the nearest available driver in the order's delivery region.

    ``restaurant_location`` remains accepted for existing callers, but assignment
    deliberately uses the location and region captured on the order. This keeps
    a pending delivery stable if a restaurant record is edited after checkout.
    """
    order = session.get(Order, order_id)
    if order is None:
        raise ValueError("Order does not exist")
    if order.order_status in {"delivered", "cancelled"}:
        raise ValueError("Completed or cancelled orders cannot be assigned")
    if order.driver_id is not None:
        return session.get(Driver, order.driver_id)
    region = order.region
    location = (order.restaurant_lat, order.restaurant_lng)
    if region is None or None in location:
        restaurant = session.get(Restaurant, order.restaurant_id)
        if restaurant is None:
            raise ValueError("Order restaurant does not exist")
        region = region or restaurant.region
        if None in location:
            location = (restaurant.lat, restaurant.lng)
    drivers = session.query(Driver).filter(
        Driver.is_available.is_(True), Driver.region == region).all()
    drivers.sort(key=lambda d: (geodesic((d.lat, d.lng), location).miles, d.id))
    for driver in drivers:
        claimed = session.execute(update(Driver).where(
            Driver.id == driver.id, Driver.is_available.is_(True),
            Driver.region == region).values(is_available=False))
        if claimed.rowcount != 1:
            continue
        assigned = session.execute(update(Order).where(
            Order.id == order_id, Order.driver_id.is_(None), Order.order_status == "pending").values(
                driver_id=driver.id, order_status="assigned"))
        if assigned.rowcount != 1:
            session.rollback()
            session.expire_all()
            current = session.get(Order, order_id)
            return session.get(Driver, current.driver_id) if current.driver_id else None
        session.commit()
        return session.get(Driver, driver.id)
    session.rollback()
    return None
