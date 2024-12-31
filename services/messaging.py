# services/messaging.py
import pika
import json
from config.config import config

class RabbitMQ:
    def __init__(self, host=None, queue="updates"):
       self.host = host or config.RABBITMQ_HOST
       self.queue = queue
       self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
       self.channel = self.connection.channel()
       self.channel.queue_declare(queue=self.queue)

    def publish(self, message):
       self.channel.basic_publish(exchange="", routing_key=self.queue, body=json.dumps(message))

    def consume(self, callback, queue=None):
       if queue:
         self.queue = queue
         self.channel.queue_declare(queue=self.queue)
       def handle_message(ch, method, properties, body):
         callback(json.loads(body.decode()))
       self.channel.basic_consume(queue=self.queue, on_message_callback=handle_message, auto_ack=True)
       self.channel.start_consuming()
