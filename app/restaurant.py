# startup/app/restaurant.py

from db.models import Restaurant
from db.connection import SessionLocal
import logging
logger = logging.getLogger('backend_logger')

class RestaurantManager:
    def __init__(self):
      pass

    def get_restaurant_by_id(self, restaurant_id: int):
        """Retrieves a restaurant by their ID."""
        session = SessionLocal()
        try:
           restaurant = session.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
           if restaurant:
                logger.info(f"retrieved restaurant by id: {restaurant.id}")
                return restaurant
           else:
               logger.warning(f"Could not find restaurant by id {restaurant_id}")
               return None

        except Exception as e:
           logger.error(f"Could not get restaurant by id: {e}")
           return None
        finally:
            session.close()

    def get_all_restaurants(self):
        """Gets all restaurant details."""
        session = SessionLocal()
        try:
            all_restaurants = session.query(Restaurant).all()
            if all_restaurants:
               logger.info(f'Found {len(all_restaurants)} restaurants')
               return all_restaurants
            else:
                logger.warning('Could not find any restaurants')
                return None

        except Exception as e:
           logger.error(f"Could not get all restaurants: {e}")
           return None

        finally:
            session.close()
    def create_restaurant(self, name: str, lat: float, lng: float, region: str, address:str, cuisine:str):
        """Creates a new restaurant."""
        session = SessionLocal()
        try:
          new_restaurant = Restaurant(name=name, lat=lat, lng=lng, region=region, address=address, cuisine=cuisine)
          session.add(new_restaurant)
          session.commit()
          logger.info(f'Created new restaurant {new_restaurant.id}')
          return new_restaurant
        except Exception as e:
          logger.error(f"Could not create restaurant : {e}")
          session.rollback()
          return None
        finally:
            session.close()

    def update_restaurant(self, restaurant_id: int, name: str = None, lat: float = None, lng: float = None,
                        region: str = None, address:str=None, cuisine:str=None):
        """Updates restaurant details."""
        session = SessionLocal()
        try:
           restaurant = session.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
           if not restaurant:
               logger.warning(f"Could not find restaurant with id: {restaurant_id}")
               return None
           if name:
              restaurant.name = name
           if lat:
              restaurant.lat = lat
           if lng:
              restaurant.lng = lng
           if region:
              restaurant.region = region
           if address:
              restaurant.address = address
           if cuisine:
              restaurant.cuisine=cuisine

           session.commit()
           logger.info(f"Updated restaurant {restaurant_id}")
           return restaurant

        except Exception as e:
           logger.error(f"Could not update restaurant: {e}")
           session.rollback()
           return None
        finally:
            session.close()
    def delete_restaurant(self, restaurant_id:int):
       """Deletes restaurant from db"""
       session = SessionLocal()
       try:
         restaurant = session.query(Restaurant).filter(Restaurant.id==restaurant_id).first()
         if not restaurant:
            logger.warning(f"Could not find restaurant by id {restaurant_id}")
            return False
         session.delete(restaurant)
         session.commit()
         logger.info(f"Deleted restaurant id {restaurant_id}")
         return True
       except Exception as e:
             logger.error(f"Could not delete restaurant by id : {restaurant_id} {e}")
             session.rollback()
             return False
       finally:
            session.close()

 # Any other restaurant facing logic can go here in the future