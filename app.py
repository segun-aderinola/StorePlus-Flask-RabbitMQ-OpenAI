from flask import Flask, request, jsonify
import openai
import os
from flask_socketio import SocketIO, emit
import json
import time
from services.order_processor import send_order_to_queue
import services.notification_service
# from 

# client = OpenAI()

app = Flask(__name__)
DATA_FILE = 'books.json'


# db = SQLAlchemy(app)
socketio = SocketIO(app)


openai.api_key = os.getenv('OPENAI_API_KEY')

def read_data():
    with open(DATA_FILE, 'r') as file:
        return json.load(file)

def write_data(data):
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)

def check_book_exist(book_id):
    get_all_books = read_data()
    get_all_books = get_all_books['books']
    book_exist = next((book for book in get_all_books if book["id"] == book_id), None)
    if(book_exist):
        return ['true', book_exist]
    else:
        return ['false']

def check_order_exist(book_id, username):
    get_all_orders = read_data()
    get_all_orders = get_all_orders['orders']
    order_exist = next((order for order in get_all_orders if order["book_id"] == book_id and order['username'] == username), None)
    if(order_exist):
        return 'true'
    else:
        return 'false'

def get_order(order_id):
    get_all_orders = read_data()
    get_all_orders = get_all_orders['orders']
    order_exist = next((order for order in get_all_orders if order["id"] == order_id), None)
    if(order_exist):
        return ['true', order_exist]
    else:
        return ['false']

def call_openai_api(book_content):
    retries = 5
    for i in range(retries):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": f"Summarize the following content: {book_content}"}
                ],
                max_tokens=100
            )
            return response.choices[0].message['content'].strip()
        except openai.error.RateLimitError as e:
            if i < retries - 1:
                time.sleep(2 ** i)
            else:
                raise e
        except openai.error.InvalidRequestError as e:
            raise e
        
@app.route('/books', methods=['GET'])
def get_books():
    get_all_books = read_data()
    return jsonify({ "status": "success", "message" : "Books retrieved successfully", "data": get_all_books['books']})

@app.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):

    book = check_book_exist(book_id)
    if book[0] == 'true':
        return jsonify({ "status": "success", "message" : "Books retrieved successfully", "data": book[1]})
    else:
        return jsonify({"status": "error" , "message": "Book not found"}), 404

@app.route('/order', methods=['POST'])
def place_order():
    try:
        order = request.json

        book_exist = check_book_exist(order['book_id'])
        if(book_exist[0] == "true"):

            order_exist = check_order_exist(order['book_id'], order['username'])
            if order_exist == 'true':
                
                return jsonify({ "message":"This username has already ordered for this book", "status": "error" }), 404

            if book_exist[1]['stock'] <= 0:
                return jsonify({'status': 'error', 'message': 'Book out of stock'}), 400
            neworder = {}
            neworder['book_id'] = order['book_id']
            neworder['status'] = "processing"
            neworder['username'] = order['username']
            neworder['order_address'] = order['order_address']

            data = read_data()

            order_id = len(data['orders']) + 1
            neworder['id'] = order_id
            data['orders'].append(neworder)
            write_data(data)
            # Send message to RabbitMQ (omitted here, will be shown later)
            send_order_to_queue({'order_id': order_id, 'book_id': book_exist[1]['id']})
            
            return jsonify({ "data": neworder, "message":"Book successfully ordered", "status": "success" }), 200
        else:
            return jsonify({ "message":"Book not found", "status": "error" }), 404
        
    except KeyError as e:
        # print(f"KeyError: {e} not found in the dictionary. Available keys are: {order_exist[1].keys()}")
        raise e
    except TypeError:
        print("An error occured")


@app.route('/order/<int:order_id>', methods=['GET'])
def get_order_status(order_id):
    data = get_order(order_id)
    if(data[0] == "false"):

        return jsonify({ "message":"Order not found", "status": "error" }), 404

    else:
        return jsonify({ "data": data[1], "message":"Order successfully retrieved", "status": "success" }), 200



@app.route('/books/<int:book_id>/summary', methods=['GET'])
def generate_summary(book_id):
    book = check_book_exist(book_id)
    if book[0] == "true":
        try:
            summary = call_openai_api(book[1]['content'])
            return jsonify({"summary": summary})
        except openai.error.RateLimitError:
            return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429
        
    return jsonify({"error": "Book not found"}), 404

# @socketio.on('connect')
# def handle_connect():
#     print('Client connected')

# @socketio.on('disconnect')
# def handle_disconnect():
#     print('Client disconnected')

# def send_order_to_queue(order_data):
#     try:

#         connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
#         channel = connection.channel()
#         channel.queue_declare(queue='order_queue')
#         channel.basic_publish(exchange='', routing_key='order_queue', body=json.dumps(order_data))
#         connection.close()

#     except pika.exceptions.AMQPConnectionError as e:
#         print(f"Error connecting to RabbitMQ: {e}")
#         raise e

if __name__ == '__main__':
    # app.run(debug=True)
    app.run(app, host='0.0.0.0', port=5000)
