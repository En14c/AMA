import hashlib, random
from faker import Faker
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


class Question(app_database.Model):
    __tablename__ = 'questions'

    id = app_database.Column(app_database.Integer, primary_key=True)
    question_content = app_database.Column(app_database.String(500))
    asker_id = app_database.Column(app_database.Integer, app_database.ForeignKey('users.id'))
    replier_id = app_database.Column(app_database.Integer, app_database.ForeignKey('users.id'))
    answer = app_database.relationship('Answer',
                                       uselist=False,
                                       backref=app_database.backref('question', lazy='joined'),
                                       lazy='joined')

class Answer(app_database.Model):
    __tablename__ = 'answers'

    id = app_database.Column(app_database.Integer, primary_key=True)
    answer_content = app_database.Column(app_database.String(500))
    question_id = app_database.Column(app_database.Integer, app_database.ForeignKey('questions.id'))

class User(UserMixin, app_database.Model):
    __tablename__ = "users"
    
    id = app_database.Column(app_database.Integer, primary_key=True)
    role_id = app_database.Column(app_database.Integer, app_database.ForeignKey('user_roles.id'))
    username = app_database.Column(app_database.String(32), unique=True)
    email = app_database.Column(app_database.String(64), unique=True)
    password_hash = app_database.Column(app_database.String(128))
    account_confirmed = app_database.Column(app_database.Boolean, default=False)
    about_me = app_database.Column(app_database.String(300))
    avatar_hash = app_database.Column(app_database.String(32))
    in_questions = app_database.relationship('Question',
                                             foreign_keys=[Question.replier_id],
                                             backref=app_database.backref('replier', lazy='joined'),
                                             lazy='dynamic')
    out_questions = app_database.relationship('Question',
                                              foreign_keys=[Question.asker_id],
                                              backref=app_database.backref('asker', lazy='joined'),
                                              lazy='dynamic')
    fake_user_questions_count = 20
    fake_user_answers_count = fake_user_questions_count - 2

    @staticmethod
    def generate_fake_users(count=100, confirm_accounts=True, user_role='user'):
        fake = Faker()
        role = Role.query.filter(Role.role_name == user_role).first()
        if not role:
            return print('[Error] unable to get user role')
        for i in range(0, count):
            user = User(username=fake.user_name(), email=fake.safe_email(),
                        about_me=fake.sentence(nb_words=50, variable_nb_words=True, 
                                               ext_word_list=None), role=role,
                        account_confirmed=confirm_accounts)
            user.password = fake.password(length=4, special_chars=True, digits=True, 
                                          upper_case=True, lower_case=True)
            app_database.session.add(user)
        app_database.session.commit()
        
    @staticmethod
    def generate_fake_questions(username, count=fake_user_questions_count):
        fake = Faker()
        user = User.query.filter(User.username == username).first()
        if not user:
            return print('[Error] no user exist with the username provided')
        for i in range(0, count):
            fake_user = User.query.offset(random.randint(0, User.query.count() - 1)).first()
            fake_user.ask_question(question_content=fake.sentence(nb_words=10, 
                                                                  variable_nb_words=True, 
                                                                  ext_word_list=None),
                                   question_recipient=user)
        app_database.session.commit()

    @staticmethod
    def generate_fake_answers(username, count=fake_user_answers_count):
        fake = Faker()
        user = User.query.filter(User.username == username).first()
        if not user:
            return print('[Error] no user exist with the username provided')
        questions = Question.query.filter(Question.replier_id == user.id)
        for i in range(0, count):
            question = questions.offset(random.randint(0, questions.count() - 1)).first()
            if not question.answer:
                user.answer_question(answer_content=fake.sentence(nb_words=10, 
                                                                  variable_nb_words=True, 
                                                                  ext_word_list=None),
                                     question=question)
        app_database.session.commit()

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

    def change_email(self, new_email):
        self.email = new_email
        self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        app_database.session.add(self)

    def generate_gravatar_uri(self, size=100, default='identicon'):
        if not self.avatar_hash:
            self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        avatar_uri = 'http://www.gravatar.com/avatar'
        return '{avatar_uri}/{hash}?s={size}&d={default}'.format(avatar_uri=avatar_uri,
                                                                 hash=self.avatar_hash,
                                                                 size=size,
                                                                 default=default)

    def ask_question(self, question_content, question_recipient):
        question = Question(question_content=question_content, asker=self, replier=question_recipient)
        app_database.session.add(question)
    
    def answer_question(self, answer_content, question):
        answer = Answer(answer_content=answer_content, question=question)
        app_database.session.add(answer)

    def get_unanswered_questions(self):
        unanswered_questions = []
        for question in Question.query.filter(Question.replier_id == self.id).all():
            if not question.answer:
                unanswered_questions.append(question)
        return unanswered_questions

    def get_answered_questions(self):
        answered_questions = []
        for question in Question.query.filter(Question.replier_id == self.id).all():
            if question.answer:
                answered_questions.append(question)
        return answered_questions