import os
from celery import Celery
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from confg import AppConfig

app_database = SQLAlchemy()
app_migrate = Migrate(db=app_database)

app_login_manager = LoginManager()
app_login_manager.session_protection = 'strong'
app_login_manager.login_view = 'auth.signin'

app_celery = Celery(__name__, broker=os.environ.get('AMA_MSG_BROKER_URI'))
app_celery.conf.update(accept_content=['json', 'pickle'])

def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    app.url_map.strict_slashes = False

    app_database.init_app(app)
    app_migrate.init_app(app)
    app_login_manager.init_app(app)
    
    from .main import main as main_blueprint
    from .auth import auth as auth_blueprint
    from .api  import api  as api_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(api_blueprint, url_prefix='/api')

    return app