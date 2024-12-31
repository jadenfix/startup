# startup/services/pricing.py
from geopy.distance import geodesic

def calculate_delivery_fee(customer_location: tuple, restaurant_location: tuple, demand_factor:float=1.0):
    distance = geodesic(customer_location, restaurant_location).miles
    base_fee = 5.0
    distance_fee = 2.0 * distance
    demand_surcharge = demand_factor * 3.0
    total_fee = base_fee + distance_fee + demand_surcharge
    return round(total_fee, 2)