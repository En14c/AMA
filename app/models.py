from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import current_app
from itsdangerous import TimedJSONWebSignatureSerializer, BadSignature, SignatureExpired
from confg import TokenExpirationTime
from . import app_database

class AppPermissions:
    ASK = 0x1
    FOLLOW_OTHERS = 0x2
    ADMINISTER = 0x4

class Role(app_database.Model):
    __tablename__ = 'user_roles'

    id = app_database.Column(app_database.Integer, primary_key=True)
    role_name = app_database.Column(app_database.String(32), unique=True)
    permissions = app_database.Column(app_database.Integer)
    users = app_database.relationship('User', backref=app_database.backref('role', lazy='joined'),
                                      lazy='dynamic')

    roles = {
        'user': AppPermissions.ASK | \
                AppPermissions.FOLLOW_OTHERS,
        'admin': AppPermissions.ASK | \
                 AppPermissions.FOLLOW_OTHERS | \
                 AppPermissions.ADMINISTER
    }

    @staticmethod
    def populate_table():
        """add/update roles to/in the user_roles table"""
        for role in Role.roles:
            role_ = Role.query.filter(Role.role_name == role).first()
            if not role_:
                role_ = Role(role_name=role)
            role_.permissions = Role.roles[role]
            app_database.session.add(role_)
            app_database.session.commit()


class User(UserMixin, app_database.Model):
    __tablename__ = "users"
    
    id = app_database.Column(app_database.Integer, primary_key=True)
    role_id = app_database.Column(app_database.Integer, app_database.ForeignKey('user_roles.id'))
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

    def has_permissions(self, permissions):
        return self.role is not None and \
                        self.role.permissions & permissions == permissions
    
    def is_admin(self):
        return self.has_permissions(AppPermissions.ADMINISTER)