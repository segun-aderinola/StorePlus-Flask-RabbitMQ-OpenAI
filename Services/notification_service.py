import pika
import json
from flask_socketio import SocketIO
from app import socketio

def notify_status_update(order_id, status):
    socketio.emit('order_status_update', {'order_id': order_id, 'status': status}, broadcast=True)

def process_notifications():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='status_queue')

    def callback(ch, method, properties, body):
        status_update = json.loads(body)
        notify_status_update(status_update['order_id'], status_update['status'])

    channel.basic_consume(queue='status_queue', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == '__main__':
    process_notifications()
