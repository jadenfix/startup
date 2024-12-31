 #   `services/driver_matching.py`
    from db.models import Driver, Order
    from sqlalchemy.orm import Session
    from geopy.distance import geodesic
    from geopy.point import Point
    from geohash import encode, decode
    import math

    def encode_geohash_to_driver_location(driver:Driver, precision=8):
        return encode(latitude=driver.lat, longitude=driver.lng, precision=precision)


    def assign_driver(session: Session, order_id: int, restaurant_location: tuple):
      try:
            available_drivers = session.query(Driver).filter(Driver.is_available == True).all()

            best_driver = None
            shortest_distance = float('inf')

            # Using Geohashing
            geohashed_drivers = {}
            for driver in available_drivers:
                driver_geohash = encode_geohash_to_driver_location(driver)
                if driver_geohash not in geohashed_drivers:
                   geohashed_drivers[driver_geohash] = []
                geohashed_drivers[driver_geohash].append(driver)

            order_geohash = encode(latitude=restaurant_location[0], longitude=restaurant_location[1])
            closest_geohash = find_closest_geohash_drivers(order_geohash, geohashed_drivers) #find a geohash bucket that is the closest to the order

            if not closest_geohash:
                print("No available drivers within a nearby geohash")
                return None
            for driver in closest_geohash:
               driver_location = (driver.lat, driver.lng)
               distance = geodesic(driver_location, restaurant_location).miles

               if distance < shortest_distance:
                   best_driver = driver
                   shortest_distance = distance

            if best_driver:
                best_driver.is_available = False
                session.commit()
                return best_driver
            else:
                print("No drivers are available.")
                return None


      except Exception as e:
          print(f"Error finding driver : {e}")
          return None


    def find_closest_geohash_drivers(order_geohash, geohashed_drivers, max_steps=2):
          try:
           geohash_bucket_order = [order_geohash] #start from the original geohash
           drivers_found = []
           steps = 0

           while drivers_found == [] and steps < max_steps:
              for current_geohash in geohash_bucket_order:
                  if current_geohash in geohashed_drivers:
                     drivers_found += geohashed_drivers[current_geohash]
                     if drivers_found:
                       return drivers_found
              steps +=1
              geohash_bucket_order = generate_neighbours_geohash(geohash=order_geohash,steps=steps)
           return drivers_found
          except Exception as e:
            print(f"Error when finding geohash buckets {e}")
            return []

    def generate_neighbours_geohash(geohash, steps=1): #generate geohash buckets adjacent to the current geohash

         try:
             point = decode(geohash)
             neighbours = []

             x = int(math.sqrt(2)) * steps
             for i in range(-x, x+1):
               for j in range(-x,x+1):
                     if i ==0 and j==0:
                         continue

                     adj_point= Point(point[0] + 0.1*i,point[1]+0.1*j) # adjust by increments for more spread.
                     neighbours.append(encode(adj_point.latitude,adj_point.longitude)) # increase size of the box by increasing this factor
             return neighbours
         except Exception as e:
             print(f"Could not generate neighbours for given geohash : {e}")
             return []