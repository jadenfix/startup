# startup/app/customer.py
from db.models import Customer
from db.connection import SessionLocal
import logging
logger = logging.getLogger('backend_logger')

class CustomerManager:
    def __init__(self):
      pass
    def get_customer_by_id(self, customer_id: int):
         """Retrieves a customer by their ID."""
         session = SessionLocal()
         try:
            customer = session.query(Customer).filter(Customer.id == customer_id).first()
            if customer:
               logger.info(f'customer retrieved {customer.id}')
               return customer
            else:
                logger.warning(f"Could not find customer by id {customer_id}")
                return None
         except Exception as e:
           logger.error(f"Error while getting customer by id: {e}")
           return None

         finally:
           session.close()
    def get_all_customers(self):
      """Gets all customer details."""
      session = SessionLocal()
      try:
          all_customers = session.query(Customer).all()
          if all_customers:
              logger.info(f"Successfully retrieved {len(all_customers)} customers.")
          else:
            logger.warning('Could not get any customers')
          return all_customers
      except Exception as e:
            logger.error(f"Error while getting all customers: {e}")
            return None
      finally:
           session.close()
    def create_customer(self, name: str, lat: float, lng: float, region: str, address:str):
          """Creates a new customer."""
          session = SessionLocal()
          try:
            new_customer = Customer(name=name, lat=lat, lng=lng, region=region, address=address)
            session.add(new_customer)
            session.commit()
            logger.info(f"Customer created with id {new_customer.id}")
            return new_customer

          except Exception as e:
           logger.error(f'Could not add customer {e}')
           session.rollback()
           return None
          finally:
              session.close()


    def update_customer(self, customer_id: int, name: str = None, lat: float = None, lng: float = None,
                        region: str = None, address:str=None):
        """Updates customer details."""
        session = SessionLocal()
        try:
            customer = session.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                logger.warning(f"Could not find customer by id : {customer_id}")
                return None
            if name:
                customer.name = name
            if lat:
                customer.lat = lat
            if lng:
                customer.lng = lng
            if region:
                customer.region = region
            if address:
                 customer.address = address

            session.commit()
            logger.info(f"Updated customer : {customer_id}")

            return customer

        except Exception as e:
          logger.error(f"Could not update customer : {e}")
          session.rollback()
          return None

        finally:
          session.close()

    def delete_customer(self, customer_id:int):
         """Deletes customer from db"""
         session = SessionLocal()
         try:
            customer = session.query(Customer).filter(Customer.id==customer_id).first()
            if not customer:
                 logger.warning(f"Could not find customer for id {customer_id}")
                 return False
            session.delete(customer)
            session.commit()
            logger.info(f"Customer deleted {customer_id}")

            return True
         except Exception as e:
             logger.error(f"Could not delete customer by id {customer_id}: {e}")
             session.rollback()
             return False

         finally:
              session.close()

# Any other customer facing logic can go here in the future such as a class for handling payments.