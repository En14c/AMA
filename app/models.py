from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import app_database


class User(UserMixin, app_database.Model):
    __tablename__ = "users"
    
    id = app_database.Column(app_database.Integer, primary_key=True)
    username = app_database.Column(app_database.String(32), unique=True)
    email = app_database.Column(app_database.String(64), unique=True)
    password_hash = app_database.Column(app_database.String(128))

    @property
    def password(self):
        raise AttributeError('password attribute is write-only')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
