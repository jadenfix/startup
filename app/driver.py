# startup/app/driver.py
from db.models import Driver
from db.connection import SessionLocal
import logging
logger = logging.getLogger('backend_logger')


class DriverManager:
    def __init__(self):
      pass
    def get_driver_by_id(self, driver_id: int):
         """Retrieves a driver by their ID."""
         session = SessionLocal()
         try:
            driver = session.query(Driver).filter(Driver.id == driver_id).first()
            if driver:
               logger.info(f"driver retrieved {driver.id}")
               return driver
            else:
                 logger.warning(f"Could not get driver by id {driver_id}")
                 return None
         except Exception as e:
            logger.error(f"Error while getting driver by id: {e}")
            return None
         finally:
             session.close()
    def get_all_drivers(self):
        """Gets all driver details."""
        session = SessionLocal()
        try:
            all_drivers = session.query(Driver).all()
            if all_drivers:
              logger.info(f"Retrieved {len(all_drivers)} drivers")

            else:
                 logger.warning('No drivers found')

            return all_drivers
        except Exception as e:
           logger.error(f"Error while getting all drivers: {e}")
           return None
        finally:
            session.close()
    def create_driver(self, name: str, lat: float, lng: float, region: str, address:str, is_available:bool):
           """Creates a new driver."""
           session = SessionLocal()
           try:
             new_driver = Driver(name=name, lat=lat, lng=lng, region=region, address=address, is_available=is_available)
             session.add(new_driver)
             session.commit()
             logger.info(f"created driver {new_driver.id}")
             return new_driver
           except Exception as e:
              session.rollback()
              logger.error(f'Could not add driver : {e}')
              return None
           finally:
               session.close()

    def update_driver(self, driver_id: int, name: str = None, lat: float = None, lng: float = None,
                       region: str = None, is_available: bool= None, address:str=None):
          """Updates driver details."""
          session = SessionLocal()
          try:
            driver = session.query(Driver).filter(Driver.id == driver_id).first()
            if not driver:
               logger.warning(f'Could not find driver to update {driver_id}')
               return None
            if name:
                driver.name = name
            if lat:
              driver.lat = lat
            if lng:
              driver.lng = lng
            if region:
               driver.region = region
            if is_available is not None: #can be true or false
                 driver.is_available = is_available
            if address:
                 driver.address = address

            session.commit()
            logger.info(f'updated driver {driver_id}')
            return driver

          except Exception as e:
               logger.error(f'Could not update driver : {e}')
               session.rollback()
               return None
          finally:
              session.close()

    def delete_driver(self, driver_id:int):
        """Deletes driver from db"""
        session = SessionLocal()
        try:
          driver = session.query(Driver).filter(Driver.id == driver_id).first()
          if not driver:
               logger.warning(f'Could not find driver to delete by id {driver_id}')
               return False
          session.delete(driver)
          session.commit()
          logger.info(f"Deleted driver id {driver_id}")
          return True
        except Exception as e:
           logger.error(f'Could not delete driver by id {driver_id} {e}')
           session.rollback()
           return False
        finally:
            session.close()

    def get_available_drivers(self):
        """Returns available drivers"""
        session = SessionLocal()
        try:
            available_drivers = session.query(Driver).filter(Driver.is_available == True).all()
            if available_drivers:
               logger.info(f"found {len(available_drivers)} drivers available")
               return available_drivers
            else:
              logger.warning("No drivers available")
              return None

        except Exception as e:
          logger.error(f"Could not find available drivers : {e}")
          return None

        finally:
           session.close()



# Any other driver facing logic can go here in the future