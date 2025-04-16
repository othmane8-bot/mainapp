from flask import Flask,render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from os import path




mail = Mail()


# Initialize database
db = SQLAlchemy()
DB_NAME = "database.db"


def create_app():
    app = Flask(__name__)

    from dotenv import load_dotenv
    import os

    load_dotenv()
    # App configuration
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'

    # Initialize extensions with the app
    db.init_app(app)
    mail.init_app(app)

    # Register blueprints
    from .views import views
    from .auth import auth
    from .calcul import calcul
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(calcul, url_prefix='/')

    # Import your models
    from .models import User

    # Create the database (if it doesn't exist)
    create_database(app)

    # Set up Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    # Configure Flask-Mail
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
    app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
    mail.init_app(app)
    return app


def create_database(app):  # <--   # Check if the database file exists in the "website" folder
    if not path.exists('website/' + DB_NAME):
        with app.app_context():
            db.create_all()
            print('Created database!')