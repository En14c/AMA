from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from .main import main as main_blueprint



app_database = SQLAlchemy()
app_migrate = Migrate(db=app_database)

app_login_manager = LoginManager()
app_login_manager.session_protection = 'strong'
app_login_manager.login_view = 'auth.signin'

def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)

    app_database.init_app(app)
    app_migrate.init_app(app)
    app_login_manager.init_app(app)

    from .main import main as main_blueprint
    from .auth import auth as auth_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    return app