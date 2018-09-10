from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import current_app
from itsdangerous import TimedJSONWebSignatureSerializer, BadSignature, SignatureExpired
from confg import TokenExpirationTime
from . import app_database


class User(UserMixin, app_database.Model):
    __tablename__ = "users"
    
    id = app_database.Column(app_database.Integer, primary_key=True)
    username = app_database.Column(app_database.String(32), unique=True)
    email = app_database.Column(app_database.String(64), unique=True)
    password_hash = app_database.Column(app_database.String(128))
    account_confirmed = app_database.Column(app_database.Boolean, default=False)

    @property
    def password(self):
        raise AttributeError('password attribute is write-only')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def create_confirmation_token(self, exp=TokenExpirationTime.AFTER_15_MIN):
        serializer = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], expires_in=exp)
        token_payload = {'account_confirmation': self.id}
        token = serializer.dumps(token_payload)
        return token
    
    def verify_confirmation_token(self, token):
        serializer = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        try:
            token_payload = serializer.loads(token)
        except (BadSignature, SignatureExpired):
            return False
        #somehow a malicious user managed to generate signed tokens
        if token_payload.get('account_confirmation') != self.id:
            return False
        self.account_confirmed = True
        app_database.session.add(self)
        return True