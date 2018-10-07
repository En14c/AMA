import hashlib, random, datetime
from werkzeug.security import generate_password_hash, check_password_hash
from faker import Faker
from flask_login import UserMixin
from flask import current_app, jsonify, url_for
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

    @staticmethod
    def load_role_by_id(role_id):
        return Role.query.get(role_id)

    @staticmethod
    def load_role_by_name(role_name):
        return Role.query.filter(Role.role_name == role_name).first()

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
    timestamp = app_database.Column(app_database.DateTime, default=datetime.datetime.utcnow)
    asker_id = app_database.Column(app_database.Integer, app_database.ForeignKey('users.id'))
    replier_id = app_database.Column(app_database.Integer, app_database.ForeignKey('users.id'))
    has_answer = app_database.Column(app_database.Boolean, default=False)
    answer = app_database.relationship('Answer',
                                       uselist=False,
                                       backref=app_database.backref('question', lazy='joined'),
                                       lazy='joined')

    @staticmethod
    def load_question_by_id(question_id):
        return Question.query.get(question_id)
    
    @staticmethod
    def load_question_by_id_or_404(question_id):
        return Question.query.get_or_404(question_id)

class Answer(app_database.Model):
    __tablename__ = 'answers'

    id = app_database.Column(app_database.Integer, primary_key=True)
    answer_content = app_database.Column(app_database.String(500))
    question_id = app_database.Column(app_database.Integer, app_database.ForeignKey('questions.id'))

class Follow(app_database.Model):
    __tablename__ = 'follows'

    id = app_database.Column(app_database.Integer, primary_key=True)
    timestamp = app_database.Column(app_database.DateTime, default=datetime.datetime.utcnow)    
    follower_id = app_database.Column(app_database.Integer, app_database.ForeignKey('users.id'))
    followed_id = app_database.Column(app_database.Integer, app_database.ForeignKey('users.id'))

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
    api_auth_token = app_database.Column(app_database.String(300))
    in_questions = app_database.relationship('Question',
                                             foreign_keys=[Question.replier_id],
                                             backref=app_database.backref('replier', lazy='joined'),
                                             lazy='dynamic')
    out_questions = app_database.relationship('Question',
                                              foreign_keys=[Question.asker_id],
                                              backref=app_database.backref('asker', lazy='joined'),
                                              lazy='dynamic')
    follows = app_database.relationship('Follow',
                                        foreign_keys=[Follow.follower_id],
                                        backref=app_database.backref('follower', lazy='joined'),
                                        lazy='dynamic',
                                        cascade='all, delete-orphan')
    followed_by = app_database.relationship('Follow',
                                            foreign_keys=[Follow.followed_id],
                                            backref=app_database.backref('followed', lazy='joined'),
                                            lazy='dynamic',
                                            cascade='all, delete-orphan')
    
    fake_user_questions_count = 20
    fake_user_answers_count = fake_user_questions_count - 2
    fake_followers_count = 20
    fake_followed_count = fake_followers_count - 2    

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
            if not question.has_answer:
                user.answer_question(answer_content=fake.sentence(nb_words=10, 
                                                                  variable_nb_words=True, 
                                                                  ext_word_list=None),
                                     question=question)
        app_database.session.commit()

    @staticmethod
    def generate_fake_followers(username, count=fake_followers_count):
        user = User.query.filter(User.username == username).first()
        if not user:
            return print('[Error] no user exist with the username provided')
        for i in range(0, count):
            follower = User.query.offset(random.randint(0, User.query.count() -1)).first()
            if not follower.is_following(user):
                follower.follow(user)
        app_database.session.commit()

    @staticmethod
    def generate_fake_followed_users(username, count=fake_followed_count):
        user = User.query.filter(User.username == username).first()
        if not user:
            return print('[Error] no user exist with the username provided')
        for i in range(0, count):
            followed = User.query.offset(random.randint(0, User.query.count() -1)).first()
            if not user.is_following(followed):
                user.follow(followed)
        app_database.session.commit()

    @staticmethod
    def load_user_by_username(username):
        return User.query.filter(User.username == username).first()

    @staticmethod
    def load_user_by_email_addr(email_addr):
        return User.query.filter(User.email == email_addr).first()

    @staticmethod
    def load_user_by_id(user_id):
        return User.query.filter(User.id == user_id).first()

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
        question.has_answer = True
        answer = Answer(answer_content=answer_content, question=question)
        app_database.session.add(answer)

    def is_question_replier(self, question):
        if self.id == question.replier.id:
            return True
        return False

    def is_question_asker(self, question):
        if self.id == question.asker.id:
            return True
        return False

    def get_unanswered_questions(self, num_questions=-1):
        unanswered_questions = []
        for question in (self.in_questions
                             .filter(Question.has_answer.is_(False))
                             .order_by(Question.timestamp.desc())
                             .limit(num_questions).all()):
            unanswered_questions.append(question)
        return unanswered_questions

    def get_answered_questions(self, num_questions=-1):
        answered_questions = []
        for question in (self.in_questions
                             .filter(Question.has_answer.is_(True))
                             .order_by(Question.timestamp.desc())
                             .limit(num_questions).all()):
            answered_questions.append(question)
        return answered_questions

    def follow(self, user):
        if self.id != user.id:
            if not self.is_following(user):
                follow = Follow(follower_id=self.id, followed_id=user.id)
                app_database.session.add(follow)

    def unfollow(self, user):
        followed = self.follows.filter(Follow.followed_id == user.id).first()
        if followed:
            app_database.session.delete(followed)

    def is_following(self, user):
        if self.follows.filter(Follow.followed_id == user.id).first():
            return True
        return False
    
    def is_followed_by(self, user):
        if self.followed_by.filter(Follow.follower_id == user.id).first():
            return True
        return False

    def get_followers_list(self):
        followers_list = []
        for follow in self.followed_by.all():
            followers_list.append(follow.follower)
        return followers_list
    
    def get_followed_users_list(self):
        followed_list = []
        for follow in self.follows.all():
            followed_list.append(follow.followed)
        return followed_list

    @staticmethod
    def api_load_user_from_auth_token(auth_token):
        return User.api_verify_auth_token(auth_token)

    @staticmethod
    def api_verify_auth_token(auth_token):
        token_verify = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        try:
            token_payload = token_verify.loads(auth_token)
        except BadSignature:
            return None
        return User.load_user_by_id(token_payload.get('auth_token_id', ''))

    def api_generate_auth_token(self, expires_in=TokenExpirationTime.AFTER_15_MIN):
        token_gen = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'],
                                                    expires_in=expires_in)
        token_payload = {'auth_token_id': self.id}
        self.api_auth_token = token_gen.dumps(token_payload).decode()
        app_database.session.add(self)
        app_database.session.commit()

    def api_get_auth_token_json(self):
        auth_token_data = {
            'auth_token': self.api_auth_token,
            'status_code': 200 
        }
        return jsonify(auth_token_data)

    def api_get_user_info(self):
        user_info = {
            'id': self.id,
            'username': self.username,
            'about_me': self.about_me,
            'avatar_uri': self.generate_gravatar_uri(),
            '#followers': self.followed_by.count(),
            '#following': self.follows.count(),
            'followers': url_for('api.api_get_followers_list', username=self.username,
                                 p=1,
                                 _external=True),
            'following': url_for('api.api_get_followed_users_list', username=self.username,
                                 p=1,
                                 _external=True),
            'account_confirmed': self.account_confirmed,
            'role': self.role.role_name,
            'status_code': 200
        }
        return user_info

    @staticmethod
    def api_get_users_list_json(page, users_per_page):
        users = User.query.paginate(page, users_per_page, False)
        next_users_list_uri = url_for('api.api_get_users_list', 
                                      n=users_per_page,
                                      p=page + 1,
                                      _external=True) if users.has_next else 'NULL'
        users_list = {
            'users': [user.api_get_user_info() for user in users.items],
            'next': next_users_list_uri,
            'status_code': 200
        }
        return jsonify(users_list)
    
    @staticmethod
    def api_get_followers_list_json(user, page, followers_per_page):
        follow = user.followed_by.paginate(page, followers_per_page, False)
        next_followers_uri = url_for('api.api_get_followers_list', 
                                     username=user.username,
                                     n=followers_per_page,
                                     p=page + 1,
                                     _external=True) if follow.has_next else 'NULL'
        followers_list = {
            'followers': [follow.follower.api_get_user_info() for follow in follow.items],
            'next': next_followers_uri,
            'status_code': 200
        }
        return jsonify(followers_list)

    @staticmethod
    def api_get_followed_users_list_json(user, page, followed_users_per_page):
        follow = user.follows.paginate(page, followed_users_per_page, False)
        next_followed_users_uri = url_for('api.api_get_followed_users_list',
                                          username=user.username,
                                          n=followed_users_per_page,
                                          p=page + 1,
                                          _external=True) if follow.has_next else 'NULL'
        followed_users_list = {
            'following': [follow.followed.api_get_user_info() for follow in follow.items],
            'next': next_followed_users_uri,
            'status_code': 200
        }
        return jsonify(followed_users_list)

    @staticmethod
    def api_get_question_info(question):
        question_info = {
            'asker': question.asker.username,
            'replier': question.replier.username,
            'question': question.question_content,
            'has_answer': question.has_answer,
            'answer': question.answer.answer_content if question.has_answer else 'NULL',
            'date': str(question.timestamp),
            'status_code': 200
        }
        return question_info

    @staticmethod
    def api_get_answered_questions_json(user, page, questions_per_page):
        questions = (user.in_questions
                         .filter(Question.has_answer.is_(True))
                         .order_by(Question.timestamp.desc())
                         .paginate(page, questions_per_page, False))
        next_questions_uri = url_for('api.api_get_user_answered_questions',
                                     username=user.username,
                                     n=questions_per_page,
                                     p=page + 1,
                                     _external=True) if questions.has_next else 'NULL'
        answered_questions_list = {
            'answered_questions': [User.api_get_question_info(q) for q in questions.items],
            'next': next_questions_uri,
            'status_code': 200
        }
        return jsonify(answered_questions_list)

    @staticmethod
    def api_get_unanswered_questions_json(user, page, questions_per_page):
        questions = (user.in_questions
                         .filter(Question.has_answer.is_(False))
                         .order_by(Question.timestamp.desc())
                         .paginate(page, questions_per_page, False))
        next_questions_uri = url_for('api.api_get_user_unanswered_questions',
                                     username=user.username,
                                     n=questions_per_page,
                                     p=page + 1,
                                     _external=True) if questions.has_next else 'NULL'
        unanswered_questions_list = {
            'unanswered_questions': [User.api_get_question_info(q) for q in questions.items],
            'next': next_questions_uri,
            'status_code': 200
        }
        return jsonify(unanswered_questions_list)