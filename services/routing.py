# `services/routing.py`
import requests
import json
from config.config import config
from cachetools import TTLCache
import logging
import random
# Use cache to store recent google api requests with 5 min expiration.
cache = TTLCache(maxsize=100, ttl=300)
logger = logging.getLogger("backend_logger")
# List of fallback routing services
ROUTING_SERVICES = [
 "https://maps.googleapis.com/maps/api/directions/json",
#can add other fallbacks here e.g. "https://router.project-osrm.org/route/v1/driving/"
]
def get_optimized_route(api_key: str, origin: str, destination: str, waypoints: list = []):
 try:
     api_key = api_key or config.GOOGLE_MAPS_API_KEY
     cache_key = (origin, destination, tuple(waypoints))

     if cache_key in cache:
         logger.info("Route found in cache")
         return cache[cache_key]
     else:
        for service in ROUTING_SERVICES: # Loop through our various APIs

          url = service

          params = {
              "origin": origin,
              "destination": destination,
               "waypoints": "|".join(waypoints),
               "key": api_key
               }
          if service.startswith('https://router.project-osrm.org/route/v1/driving'):
             params = {} #if we are calling an OSRM route endpoint for example, change this logic for whatever fall back url.
             url = f"{service}/{origin},{destination}"
             try:
                response = requests.get(url) #call the endpoint directly without additional parameters.
                response.raise_for_status()
                routes = response.json()["routes"]
                cache[cache_key] = routes # add routes to cache
                return routes

             except requests.exceptions.RequestException as e:
                logger.error(f"Could not call OSRM Service : {e}")

                continue #attempt another route provider.


          try:
               response = requests.get(url, params=params) # call google maps API (or other) as is.
               response.raise_for_status()
               routes = response.json()["routes"]
               cache[cache_key] = routes
               return routes
          except requests.exceptions.RequestException as e:
                logger.error(f"Could not fetch google maps api response : {e}")
                continue # attempt other routing providers


        return {"error": "Could not fetch any routing providers"}#if no response from all routing providers.

 except json.JSONDecodeError:
    return {"error": "Could not decode json body"}
 except KeyError:
    return {"error":"Could not find key in routing provider response"}
 except Exception as e:
     return {"error": f"General Exception in get_optimized_route {e}"}