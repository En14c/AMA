from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .main import main as main_blueprint



app_database = SQLAlchemy()
app_migrate = Migrate(db=app_database)


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)

    app_database.init_app(app)
    app_migrate.init_app(app)

    app.register_blueprint(main_blueprint)

    return app