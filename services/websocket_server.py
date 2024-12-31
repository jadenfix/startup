# startup/services/websocket_server.py
import asyncio
import websockets
import json
from services.messaging import RabbitMQ
from config.config import config

connected_clients = set()

async def notify_clients(message):
    if connected_clients:
        await asyncio.wait([client.send(json.dumps(message)) for client in connected_clients])

async def websocket_handler(websocket, path):
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            print(f"Received from client: {message}")
    except websockets.ConnectionClosed:
        pass
    finally:
        connected_clients.remove(websocket)

def rabbitmq_listener():
    rabbitmq = RabbitMQ()

    def forward_to_clients(message):
        asyncio.run(notify_clients(message))

    rabbitmq.consume(callback=forward_to_clients, queue="updates")

async def main():
    websocket_server = websockets.serve(websocket_handler, config.WEBSOCKET_HOST, config.WEBSOCKET_PORT)
    await asyncio.gather(websocket_server, asyncio.to_thread(rabbitmq_listener))

if __name__ == "__main__":
    asyncio.run(main())