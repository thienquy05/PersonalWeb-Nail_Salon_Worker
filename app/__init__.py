from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_bcrypt import Bcrypt
from config import Config

db = SQLAlchemy()
mail = Mail()
bcrypt = Bcrypt()
limiter = Limiter(key_func=get_remote_address)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    limiter.init_app(app)
    db.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)

    from app.routes import main, admin
    app.register_blueprint(main)
    app.register_blueprint(admin, url_prefix="/admin")

    return app
