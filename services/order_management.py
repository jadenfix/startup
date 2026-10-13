# startup/services/order_management.py
from db.models import Order, Customer, Restaurant, Driver
from sqlalchemy.orm import Session
from sqlalchemy import update

def create_order(session: Session, customer_id: int, restaurant_id: int):
    customer = session.get(Customer, customer_id)
    restaurant = session.get(Restaurant, restaurant_id)
    if customer is None or restaurant is None:
        raise ValueError("Customer or restaurant does not exist")
    new_order = Order(customer_id=customer_id, restaurant_id=restaurant_id,
                      customer_lat=customer.lat, customer_lng=customer.lng,
                      restaurant_lat=restaurant.lat, restaurant_lng=restaurant.lng,
                      region=restaurant.region)
    session.add(new_order)
    session.commit()
    return new_order


def update_order_status(session: Session, order_id: int, status: str):
    allowed = {"pending": {"cancelled"}, "assigned": {"delivered", "cancelled"},
               "delivered": set(), "cancelled": set()}
    for _ in range(3):
        session.expire_all()
        order = session.get(Order, order_id)
        if order is None:
            return None
        if order.order_status == status:
            return order
        if status not in allowed.get(order.order_status, set()):
            raise ValueError(f"Cannot change {order.order_status} order to {status}")
        driver_id = order.driver_id
        changed = session.execute(update(Order).where(
            Order.id == order_id, Order.order_status == order.order_status,
            Order.driver_id == driver_id).values(order_status=status))
        if changed.rowcount != 1:
            session.rollback()
            continue
        if driver_id is not None:
            session.execute(update(Driver).where(Driver.id == driver_id).values(is_available=True))
        session.commit()
        return session.get(Order, order_id)
    raise ValueError("Order changed concurrently; retry the status request")
