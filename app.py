import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import eventlet # Required by Flask-SocketIO

# --- Configuration ---

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key_change_me')

# Get database connection details from environment variables
DB_USER = os.getenv("DATABASE_USER", "root")
DB_PASSWORD = os.getenv("DATABASE_PASSWORD", "password")
DB_HOST = os.getenv("DATABASE_HOST", "db")
DB_NAME = os.getenv("MYSQL_DATABASE", "chat_db")

# Construct the database URI
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
socketio = SocketIO(app, async_mode='eventlet')
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --- Models ---

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    messages = db.relationship('Message', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

# --- Flask-Login User Loader ---

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Routes ---

@app.before_request
def create_tables():
    # Attempt to create tables on first request if they don't exist
    try:
        db.create_all()
    except Exception as e:
        # Print error but allow request to continue (if connection established)
        print(f"Error creating tables (DB might be initializing): {e}")

@app.route('/')
@login_required
def index():
    # Load last 50 messages
    messages = Message.query.order_by(Message.timestamp.desc()).limit(50).all()
    # Reverse to show newest at the bottom
    messages.reverse()
    return render_template('index.html', messages=messages, current_user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('index.html', page='login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return redirect(url_for('register'))
            
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('index'))
        
    return render_template('index.html', page='register')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# --- SocketIO Handlers ---

@socketio.on('connect')
def handle_connect():
    if not current_user.is_authenticated:
        # Disconnect unauthenticated users immediately
        return False 
    print(f'Client connected: {current_user.username}')

@socketio.on('send_message')
@login_required
def handle_send_message(data):
    message_content = data['message'].strip()
    if not message_content:
        return

    # 1. Save to database
    new_message = Message(content=message_content, user_id=current_user.id)
    db.session.add(new_message)
    db.session.commit()

    # 2. Broadcast the message to all connected clients
    message_package = {
        'username': current_user.username,
        'content': message_content,
        'is_self': False # This will be fixed on the client-side 
    }
    # Emit to everyone including the sender
    emit('new_message', message_package, broadcast=True)

# --- Run App ---
if __name__ == '__main__':
    # Use eventlet to serve the application for real-time capabilities
    socketio.run(app, host='0.0.0.0', port=5000)
