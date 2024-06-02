# Online Bookstore Asynchronous Communication System

## API Development
- Developed a REST API using Flask for fetching books, placing orders, and checking order status.
- Integrated OpenAI API for generating book summaries.

## Messaging System
- Used RabbitMQ for message passing between order processing and inventory management services.
- Orders placed are sent to RabbitMQ which handles the communication between services.

## Real-time Notifications
- Implemented real-time order status notifications using Flask-SocketIO.
- Users receive updates on their order status via WebSocket connections.

## AI-Powered Features
- Used OpenAI's gpt-3.5-turbo model to generate summaries of book content.
- This enhances user experience by providing quick overviews of books.

## How to Run
1. Ensure Docker and Docker Compose are installed.
2. Place your OpenAI API key in the `.env` or `docker-compose.yml` file.
3. Run `docker-compose up --build` to start the services.
4. The Flask API will be available at `http://localhost:5000`.
