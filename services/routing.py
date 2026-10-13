"""Bounded Google Directions requests with a five-minute cache."""
import requests
from cachetools import TTLCache
from config.config import config

cache = TTLCache(maxsize=100, ttl=300)


def get_optimized_route(api_key, origin, destination, waypoints=None):
    waypoints = waypoints or []
    api_key = api_key or config.GOOGLE_MAPS_API_KEY
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY is required for live routing"}
    key = (api_key, origin, destination, tuple(waypoints))
    if key in cache:
        return cache[key]
    try:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/directions/json",
            params={"key": api_key, "origin": origin, "destination": destination,
                    "waypoints": "|".join(waypoints)}, timeout=10)
        response.raise_for_status()
        body = response.json()
        if body.get("status", "OK") != "OK":
            return {"error": "Routing provider could not find a route"}
        routes = body["routes"]
        cache[key] = routes
        return routes
    except (requests.RequestException, ValueError, KeyError):
        return {"error": "Routing provider request failed"}
