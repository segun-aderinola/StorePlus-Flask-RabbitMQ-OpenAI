from flask import Flask, request, jsonify
from flask_socketio import SocketIO
import json

app = Flask(__name__)
socketio = SocketIO(app)

DATA_FILE = 'books.json'

def read_data():
    with open(DATA_FILE, 'r') as file:
        return json.load(file)

def write_data(data):
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@app.route('/orders', methods=['POST'])
def update_order_status(order_id):
    data = read_data()
    order = next((order for order in data['orders'] if order["id"] == order_id), None)
    if order:
        order['status'] = request.json.get('status', order['status'])
        write_data(data)
        socketio.emit('order_status', {'order_id': order_id, 'status': order['status']})
        return jsonify({"status": "success", "message":"Order status changed", "data": order}), 200
    return jsonify({"error": "Order not found"}), 404

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)

