"""Exercise the real local HTTP API and verify persistence after server restart."""
import json
import sys
import tempfile
import threading
from pathlib import Path

import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.serving import make_server

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from api.api_routes import create_app
from app.seed import seed
from db.models import Base


def serve(factory):
    server = make_server("127.0.0.1", 0, create_app(factory))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, f"http://127.0.0.1:{server.server_port}"


def main():
    with tempfile.TemporaryDirectory() as directory:
        engine = create_engine(f"sqlite:///{directory}/delivery.db")
        Base.metadata.create_all(engine)
        factory = sessionmaker(bind=engine, expire_on_commit=False)
        with factory() as session:
            seed(session)
        server, thread, url = serve(factory)
        try:
            def post(path, payload=None):
                response = requests.post(url + path, json=payload, timeout=5)
                response.raise_for_status()
                print(path, json.dumps(response.json()), flush=True)
                return response.json()
            post("/pricing", {"customer_location": [37.77, -122.42], "restaurant_location": [37.80, -122.41]})
            order = post("/orders", {"customer_id": 1, "restaurant_id": 1})
            oid = order["order_id"]
            assert post(f"/drivers/assign/{oid}")["driver_id"] == 1
            assert post(f"/drivers/assign/{oid}")["driver_id"] == 1
            delivered = requests.patch(url + f"/orders/{oid}/status", json={"status": "delivered"}, timeout=5)
            delivered.raise_for_status()
            assert delivered.json()["status"] == "delivered"
            print("Delivered:", json.dumps(delivered.json()), flush=True)
        finally:
            server.shutdown()
            thread.join()
            server.server_close()
            engine.dispose()
        # Reopen the database and server, so this tests more than an ORM identity cache.
        engine = create_engine(f"sqlite:///{directory}/delivery.db")
        factory = sessionmaker(bind=engine, expire_on_commit=False)
        server, thread, url = serve(factory)
        try:
            response = requests.get(url + f"/orders/{oid}", timeout=5)
            response.raise_for_status()
            assert response.json()["status"] == "delivered"
            assert response.json()["driver_id"] == 1
            print("Restarted API:", json.dumps(response.json()), flush=True)
            print("PASS: price → create → assign → repeat → deliver → restart → persisted order")
        finally:
            server.shutdown()
            thread.join()
            server.server_close()
            engine.dispose()


if __name__ == "__main__":
    main()
