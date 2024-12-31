# config/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
         self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./food_delivery.db")
         self.RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
         self.WEBSOCKET_HOST = os.getenv("WEBSOCKET_HOST", "localhost")
         self.WEBSOCKET_PORT = int(os.getenv("WEBSOCKET_PORT", 8765))
         self.PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", 8000))
         self.ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "localhost")
         self.ELASTICSEARCH_PORT = int(os.getenv("ELASTICSEARCH_PORT", 9200))
         self.GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


    @staticmethod
    def load_env():
       load_dotenv()
config = Config()
