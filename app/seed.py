"""Seed an empty local database for the delivery example."""
from db.connection import SessionLocal, init_db
from db.models import Customer, Driver, Order, Restaurant


def seed(session):
    if any(session.query(model).first() is not None for model in (Customer, Restaurant, Driver, Order)):
        raise ValueError("Demo seeding requires an empty database")
    session.add_all([
        Customer(id=1, name="Jaden", lat=37.77, lng=-122.42, region="SF"),
        Restaurant(id=1, name="North Beach Kitchen", lat=37.80, lng=-122.41, region="SF"),
        Driver(id=1, name="Alex", lat=37.801, lng=-122.410, region="SF"),
        Driver(id=2, name="Sam", lat=37.75, lng=-122.45, region="SF"),
        # Geographically closer, but intentionally ineligible for an SF order.
        Driver(id=3, name="Morgan", lat=37.8001, lng=-122.4101, region="OAK"),
    ])
    session.commit()


if __name__ == "__main__":
    init_db()
    with SessionLocal() as session:
        seed(session)
    print("Seeded customer 1, restaurant 1, two SF drivers, and one OAK driver.")
