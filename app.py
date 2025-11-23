# app.py

import os
from flask import Flask, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
import eventlet

# --- CONFIGURATION ---

# Read DB connection details from environment variables (set by Docker Compose)
DB_USER = os.environ.get('DATABASE_USER', 'placeholder_user')
DB_PASS = os.environ.get('DATABASE_PASSWORD', 'placeholder_pass')
DB_HOST = os.environ.get('DATABASE_HOST', 'db') 
DB_NAME = os.environ.get('MYSQL_DATABASE', 'chat_db') 

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Initialize SocketIO for real-time communication
socketio = SocketIO(app, async_mode='eventlet', manage_session=False, cors_allowed_origins="*")

# --- DATABASE MODEL ---

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())

# --- ROUTES & SOCKETIO HANDLERS ---

@app.route('/')
def index():
    # Load past messages from the database
    messages = Message.query.order_by(Message.timestamp.asc()).all()
    # Simple HTML/JS template for the chat interface
    return render_template_string("""
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.0/socket.io.js"></script>
        <h1>Real-Time Chat App</h1>
        <div id="messages">
            {% for msg in messages %}
                <p>{{ msg.text }}</p>
            {% endfor %}
        </div>
        <input id="chat-input" type="text" placeholder="Type message...">
        <button onclick="sendMessage()">Send</button>
        <script>
            var socket = io();
            document.getElementById('chat-input').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') { sendMessage(); }
            });
            function sendMessage() {
                var input = document.getElementById('chat-input');
                socket.emit('message', input.value);
                input.value = '';
            }
            socket.on('response', function(msg) {
                document.getElementById('messages').innerHTML += '<p><strong>New:</strong> ' + msg + '</p>';
                window.scrollTo(0, document.body.scrollHeight);
            });
        </script>
    """, messages=messages)

@socketio.on('message')
def handle_message(data):
    # Save message to MySQL
    new_message = Message(text=data)
    db.session.add(new_message)
    db.session.commit()
    
    # Broadcast the message to all connected clients
    emit('response', data, broadcast=True)

# --- APPLICATION RUNNER ---

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Use socketio.run for the eventlet server
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)