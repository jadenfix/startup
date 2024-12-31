# startup/services/order_management.py
from db.models import Order
from sqlalchemy.orm import Session

def create_order(session: Session, customer_id: int, restaurant_id: int):
    new_order = Order(customer_id=customer_id, restaurant_id=restaurant_id)
    session.add(new_order)
    session.commit()
    return new_order


def update_order_status(session: Session, order_id: int, status: str):
    order = session.query(Order).filter(Order.id == order_id).first()
    if order:
        order.order_status = status
        session.commit()
        return order
    return None