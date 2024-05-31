import pika
import json
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'
db = SQLAlchemy(app)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=10)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='processing')

def update_inventory(order):
    book = Book.query.get(order['book_id'])
    if book.stock > 0:
        book.stock -= 1
        db.session.commit()
        update_order_status(order['order_id'], 'completed')
    else:
        update_order_status(order['order_id'], 'failed')

def update_order_status(order_id, status):
    order = Order.query.get(order_id)
    order.status = status
    db.session.commit()
    notify_status_update(order_id, status)

def notify_status_update(order_id, status):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='status_queue')
    channel.basic_publish(exchange='', routing_key='status_queue', body=json.dumps({'order_id': order_id, 'status': status}))
    connection.close()

def process_orders():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='order_queue')

    def callback(ch, method, properties, body):
        order = json.loads(body)
        update_inventory(order)

    channel.basic_consume(queue='order_queue', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == '__main__':
    db.create_all()
    process_orders()
