import os
import eventlet
eventlet.monkey_patch()  # for Flask-SocketIO with eventlet

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    current_user, login_required
)
from werkzeug.security import generate_password_hash, check_password_hash
from authlib.integrations.flask_client import OAuth

# -------------------------------------------------------------------
# FLASK APP + CONFIG
# -------------------------------------------------------------------

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key_change_me')

# DB config from environment (works with your docker-compose)
DB_USER = os.getenv("DATABASE_USER", "root")
DB_PASSWORD = os.getenv("DATABASE_PASSWORD", "password")
DB_HOST = os.getenv("DATABASE_HOST", "db")
DB_NAME = os.getenv("MYSQL_DATABASE", "chat_db")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
socketio = SocketIO(app, async_mode='eventlet')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# OAuth setup
oauth = OAuth(app)
# You MUST set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your env/Jenkins
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/v2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={'scope': 'openid email profile'}
)

# -------------------------------------------------------------------
# MODELS
# -------------------------------------------------------------------

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)

    # for local auth
    username = db.Column(db.String(80), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=True)

    # for google auth
    email = db.Column(db.String(120), unique=True, nullable=True)
    oauth_provider = db.Column(db.String(50), nullable=True)
    oauth_id = db.Column(db.String(200), nullable=True)

    messages = db.relationship('Message', backref='author', lazy='dynamic')

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)


class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


# -------------------------------------------------------------------
# LOGIN MANAGER
# -------------------------------------------------------------------

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -------------------------------------------------------------------
# DB CREATION
# -------------------------------------------------------------------

@app.before_first_request
def create_tables():
    try:
        db.create_all()
    except Exception as e:
        print(f"Error creating tables (DB might be initializing): {e}")


# -------------------------------------------------------------------
# ROUTES – GENERAL
# -------------------------------------------------------------------

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))


# -------------------------------------------------------------------
# LOCAL AUTH ROUTES
# -------------------------------------------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('chat'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        if not username:
            flash('Username is required.', 'error')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('register'))

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for('chat'))

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# -------------------------------------------------------------------
# GOOGLE AUTH ROUTES
# -------------------------------------------------------------------

@app.route('/login/google')
def google_login():
    # redirect URI must match exactly what you configure in Google Console
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/auth/google/callback')
def google_callback():
    token = google.authorize_access_token()
    userinfo = google.get('userinfo').json()

    google_id = userinfo.get('sub')
    email = userinfo.get('email')
    name = userinfo.get('name') or email

    if not google_id:
        flash('Google login failed.', 'error')
        return redirect(url_for('login'))

    # find existing user or create
    user = User.query.filter_by(oauth_provider='google', oauth_id=google_id).first()
    if not user:
        # also check if someone with that email already exists
        user = User.query.filter_by(email=email).first()
        if user:
            # upgrade that account to have Google info
            user.oauth_provider = 'google'
            user.oauth_id = google_id
        else:
            user = User(
                username=name,
                email=email,
                oauth_provider='google',
                oauth_id=google_id
            )
            db.session.add(user)

        db.session.commit()

    login_user(user)
    return redirect(url_for('chat'))


# -------------------------------------------------------------------
# CHAT ROUTE (MAIN PAGE)
# -------------------------------------------------------------------

@app.route('/chat')
@login_required
def chat():
    # last 50 messages
    messages = (
        Message.query.order_by(Message.timestamp.desc())
        .limit(50)
        .all()
    )
    messages.reverse()  # show oldest at top, newest at bottom
    return render_template('chat.html', messages=messages)


# -------------------------------------------------------------------
# SOCKET.IO HANDLERS
# -------------------------------------------------------------------

@socketio.on('connect')
def handle_connect():
    if not current_user.is_authenticated:
        return False  # disconnect
    print(f'Client connected: {current_user.username}')


@socketio.on('send_message')
@login_required
def handle_send_message(data):
    message_content = data.get('message', '').strip()
    if not message_content:
        return

    # Save to DB
    new_message = Message(content=message_content, user_id=current_user.id)
    db.session.add(new_message)
    db.session.commit()

    # Broadcast to all
    payload = {
        'username': current_user.username,
        'content': message_content,
    }
    emit('new_message', payload, broadcast=True)


# -------------------------------------------------------------------
# RUN
# -------------------------------------------------------------------

if __name__ == '__main__':
    # In Docker your host='0.0.0.0' is correct
    socketio.run(app, host='0.0.0.0', port=5000)
