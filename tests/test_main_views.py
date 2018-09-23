import unittest, time
from werkzeug.exceptions import Forbidden, NotFound
from faker import Faker
from itsdangerous import TimedJSONWebSignatureSerializer
from flask import url_for
from app import app_database, create_app
from app.models import User, Role, AppPermissions
from confg import app_config, TokenExpirationTime

class TestMainViews(unittest.TestCase):
    def setUp(self):
        self.app = create_app(app_config['testing'])
        self.app_ctx = self.app.app_context()
        self.app_ctx.push()
        app_database.create_all()

    def tearDown(self):
        app_database.session.remove()
        app_database.drop_all()
        self.app_ctx.pop()

    
    def test_home_to_signin_redirect(self):
        """ test home page requires logged in user """
        with self.app.test_request_context():
            with self.app.test_client(use_cookies=False) as app_test_client:
                response = app_test_client.get(url_for('main.home'))
                self.assertTrue(response.status_code == 302)
        
        testuser = User(username='testuser', account_confirmed=True)
        testuser.password = '123'
        app_database.session.add(testuser)
        app_database.session.commit()
        with self.app.test_request_context():
            with self.app.test_client() as app_test_client:
                response = app_test_client.post(url_for('auth.signin'), data={
                    'username' : 'testuser', 'password' : '123'}, follow_redirects=True)
                self.assertTrue('testing-home-AMA' in response.get_data(as_text=True))

                response = app_test_client.get(url_for('main.home'))
                self.assertTrue('testing-home-AMA' in response.get_data(as_text=True))

    def test_user_profile(self):
        '''
        test 3 cases:
            [1] login required
            [2] user is logged in and requests a valid user profile
            [3] user is loggd in and requests invalid user profile
        '''
        testuser0 = User(username='testuser0', email='test@mail.com', account_confirmed=True)
        testuser0.password = '123'
        app_database.session.add(testuser0)
        app_database.session.commit()

        with self.app.test_request_context():
            with self.app.test_client() as app_test_client:
                #case [1]
                response = app_test_client.get(url_for('main.user_profile', 
                                                       username=testuser0.username), 
                                               follow_redirects=True)
                self.assertTrue('testing-signin-AMA' in response.get_data(as_text=True))

                app_test_client.post(url_for('auth.signin'), data={'username': testuser0.username,
                                                                   'password': '123'})

                #case [2]
                response = app_test_client.get(url_for('main.user_profile', 
                                                       username=testuser0.username))
                self.assertTrue('testing-user-profile-AMA' in response.get_data(as_text=True))

                #case [3]
                response = app_test_client.get(url_for('main.user_profile', 
                                                       username='foouser'))
                self.assertTrue(response.status_code == 404)

    def test_user_profile_edit(self):
        '''
        test 4 cases:
            [1] login required
            [2] current user must be the same as the target user
            [3] form validation error (new username is associated with another user)
            [4] form validation success
             +
             +-----> (1) new username is not associated with another user
                      +
                      +-----> {1} with new bio (about_me) or the same old one
                              {2} with new empty bio
        '''
        testuser0 = User(username='testuser0', email='test0@mail.com', account_confirmed=True)
        testuser1 = User(username='testuser1', email='test1@mail.com', account_confirmed=True)
        testuser0.password = '123'
        app_database.session.add_all([testuser0, testuser1])
        app_database.session.commit()

        with self.app.test_request_context():
            with self.app.test_client() as app_test_client:
                #case [1]
                response = app_test_client.get(url_for('main.user_profile_edit', 
                                                       username=testuser0.username), 
                                               follow_redirects=True)
                self.assertTrue('testing-signin-AMA' in response.get_data(as_text=True))

                app_test_client.post(url_for('auth.signin'), data={
                    'username': testuser0.username, 'password': '123'})

                response = app_test_client.get(url_for('main.user_profile_edit',
                                                       username=testuser0.username))
                self.assertTrue('testing-user-profile-edit-AMA' in response.get_data(as_text=True))

                #case [2]
                response = app_test_client.get(url_for('main.user_profile_edit', 
                                                       username=testuser1.username))
                self.assertTrue(response.status_code == 404)

                #case [3]
                response = app_test_client.post(url_for('main.user_profile_edit',
                                                        username=testuser0.username), 
                                                data={
                                                    'username': testuser1.username,
                                                })
                self.assertTrue('testing-user-profile-edit-AMA' in response.get_data(as_text=True))

                #case [4] (1) {1}
                response = app_test_client.post(url_for('main.user_profile_edit',
                                                        username=testuser0.username), 
                                                data={
                                                    'username': 'testuser0new0',
                                                    'about_me': 'foobio'
                                                }, follow_redirects=True)
                self.assertTrue('testing-user-profile-AMA' in response.get_data(as_text=True))

                response = app_test_client.post(url_for('main.user_profile_edit',
                                                        username=testuser0.username), 
                                                data={
                                                    'username': 'testuser0new1'
                                                }, follow_redirects=True)
                self.assertTrue('testing-user-profile-AMA' in response.get_data(as_text=True))
                
                #case [4](1) {2}
                response = app_test_client.post(url_for('main.user_profile_edit',
                                                        username=testuser0.username), 
                                                data={
                                                    'username': 'testuser0new2',
                                                    'about_me': ''
                                                }, follow_redirects=True)
                self.assertTrue('testing-user-profile-AMA' in response.get_data(as_text=True))

    def test_accounts_control(self):
        '''
        test 3 cases:
            [1] login required
            [2] user is not admin => 403 (forbidden)
            [3] user is admin
             +
             +-----> (1) submits a valid username
                     (2) submits invalid username
        '''
        Role.populate_table()
        admin_role = Role.query.filter(Role.role_name == 'admin').first()
        user_role = Role.query.filter(Role.role_name == 'user').first()
        admin = User(username='admin0', email='admin0@mail.com', account_confirmed=True,
                     role=admin_role)
        testuser = User(username='testuser', email='testuser@mail.com', account_confirmed=True,
                        role=user_role)
        admin.password = testuser.password = '123'
        app_database.session.add_all([admin, testuser])
        app_database.session.commit()

        with self.app.test_request_context():
            with self.app.test_client() as app_test_client:
                #case [1]
                response = app_test_client.get(url_for('main.accounts_control'), follow_redirects=True)
                self.assertTrue('testing-signin-AMA' in response.get_data(as_text=True))

                app_test_client.post(url_for('auth.signin'), data={
                    'username': testuser.username, 'password': '123'})
                
                #case [2]
                response = app_test_client.get(url_for('main.accounts_control'))
                self.assertTrue(response.status_code == 403)

                app_test_client.get(url_for('auth.signout'))

                app_test_client.post(url_for('auth.signin'), data={
                    'username': admin.username, 'password': '123'})

                response = app_test_client.get(url_for('main.accounts_control'))
                self.assertTrue('testing-accounts-control-AMA' in response.get_data(as_text=True))

                #case [3](1)
                response = app_test_client.post(url_for('main.accounts_control'), data={
                    'username': testuser.username})
                self.assertTrue(response.status_code == 302)

                #case [3](2)
                response = app_test_client.post(url_for('main.accounts_control'), data={
                    'username': 'foouser'})
                self.assertFalse(response.status_code == 302)
    
    def test_user_account_control(self):
        '''
        test 4 cases:
            [1] login required / admin permissions required for the view function
            [2] token is invalid
            [3] token is valid but no user exits with the username supplied in the (uri)
            [4] token is valid and user exits with the username supplied in the (uri)
             +
             +-------> (1) form validation error (new email is already registered)
                       (2) no form validation error (new email is availabe)
        '''
        Role.populate_table()
        admin_role = Role.query.filter(Role.role_name == 'admin').first()
        user_role = Role.query.filter(Role.role_name == 'user').first()
        admin = User(username='admin0', email='admin@mail.com', account_confirmed=True,
                     role=admin_role)
        testuser = User(username='testuser', email='testuser@mail.com', account_confirmed=True,
                        role=user_role)
        admin.password = testuser.password = '123'
        app_database.session.add_all([admin, testuser])
        app_database.session.commit()

        token_gen = TimedJSONWebSignatureSerializer(self.app.config['SECRET_KEY'], 
                                                    expires_in=TokenExpirationTime.AFTER_1_HOUR)
        token_payload = {'bar': 'foo'}
        token = token_gen.dumps(token_payload)

        with self.app.test_request_context():
            with self.app.test_client() as app_test_client:
                #case [1]
                response = app_test_client.get(url_for('main.user_account_control',
                                                       username=testuser.username, token=token), 
                                               follow_redirects=True)
                self.assertTrue('testing-signin-AMA' in response.get_data(as_text=True))
                
                app_test_client.post(url_for('auth.signin'), data={'username': testuser.username,
                                                                   'password': '123'})

                response = app_test_client.get(url_for('main.user_account_control', 
                                                       token=token, username=testuser.username))
                self.assertTrue(response.status_code == 403)

                app_test_client.get(url_for('auth.signout'))

                app_test_client.post(url_for('auth.signin'), data={'username': admin.username,
                                                                   'password': '123'})
                
                response = app_test_client.get(url_for('main.user_account_control', 
                                                       token=token, username=testuser.username))
                self.assertTrue('testing-user-account-control-AMA' in response.get_data(as_text=True))

                #case [2]
                invalid_token_gen = TimedJSONWebSignatureSerializer(self.app.config['SECRET_KEY'], 
                                                                    expires_in=TokenExpirationTime.AFTER_0_MIN)
                invalid_token = invalid_token_gen.dumps(token_payload)
                time.sleep(5)
                response = app_test_client.get(url_for('main.user_account_control', 
                                                       token=invalid_token, username=testuser.username))
                self.assertTrue(response.status_code == 404)

                #case [3]
                response = app_test_client.get(url_for('main.user_account_control',
                                                       token=token, username='invalid_username'))
                self.assertTrue(response.status_code == 404)

                #case [4](1)
                response = app_test_client.post(url_for('main.user_account_control',
                                                        token=token, username=testuser.username), 
                                                data={'email': admin.email,
                                                      'account_confirmation': True,
                                                      'user_role': user_role.id}, follow_redirects=True)
                self.assertTrue('testing-user-account-control-AMA' in response.get_data(as_text=True))

                #case [4] (2)
                response = app_test_client.post(url_for('main.user_account_control',
                                                        token=token, username=testuser.username), 
                                                data={'email': 'new@mail.com',
                                                      'account_confirmation': True,
                                                      'user_role': user_role.id}, follow_redirects=True)
                self.assertTrue('testing-user-profile-AMA' in response.get_data(as_text=True))

    def test_user_ask_question(self):
        '''
        test 5 cases:
            [1] user must be logged in
            [2] user has the permissions to ask questions
            [3] user's username is the same as the one in the uri [user is asking himself] (not allowed)
            [4] user is requesting to ask a non-existent user
            [5] 1 <= question's length <= 500
        '''
        fake = Faker()
        Role.populate_table()
        User.generate_fake_users(count=2)
        testuser1, testuser2 = User.query.get(1), User.query.get(2)
        testuser1.password = '123'

        with self.app.test_request_context():
            with self.app.test_client() as app_test_client:
                #case [1]
                response = app_test_client.get(url_for('main.user_ask_question', 
                                                       username=testuser2.username),
                                               follow_redirects=True)
                self.assertTrue('testing-signin-AMA' in response.get_data(as_text=True))

                app_test_client.post(url_for('auth.signin'), data={'username': testuser1.username,
                                                                   'password': '123'})
                
                response = app_test_client.get(url_for('main.user_ask_question',
                                                       username=testuser2.username))
                self.assertTrue('testing-ask-question-form-AMA' in response.get_data(as_text=True))

                #case [2]
                testuser1.role.permissions &= AppPermissions.FOLLOW_OTHERS
                response = app_test_client.get(url_for('main.user_ask_question',
                                                       username=testuser2.username))
                self.assertEqual(response.status_code, Forbidden.code)
                testuser1.role.permissions = Role.roles['user']

                #case [3]
                response = app_test_client.get(url_for('main.user_ask_question',
                                                       username=testuser1.username),
                                               follow_redirects=True)
                self.assertTrue('testing-home-AMA' in response.get_data(as_text=True))

                #case [4]
                response = app_test_client.get(url_for('main.user_ask_question',
                                                       username=fake.user_name()))
                self.assertEqual(response.status_code, NotFound.code)

                #case [5]
                question_content_void = ''
                question_content_long = fake.sentence(nb_words=600, 
                                                      variable_nb_words=True, ext_word_list=None)
                question_content_short = fake.sentence(nb_words=50, 
                                                       variable_nb_words=True, ext_word_list=None)
                
                response = app_test_client.post(url_for('main.user_ask_question',
                                                        username=testuser2.username), 
                                                data={'question': question_content_void})
                self.assertTrue('testing-ask-question-form-AMA' in response.get_data(as_text=True))

                response = app_test_client.post(url_for('main.user_ask_question',
                                                        username=testuser2.username), 
                                                data={'question': question_content_long})
                self.assertTrue('testing-ask-question-form-AMA' in response.get_data(as_text=True))

                response = app_test_client.post(url_for('main.user_ask_question',
                                                        username=testuser2.username), 
                                                data={'question': question_content_short},
                                                follow_redirects=True)
                self.assertTrue('testing-home-AMA' in response.get_data(as_text=True))

                #confirm the database transaction
                self.assertIsNotNone(testuser2.in_questions.first())
                self.assertIsNotNone(testuser1.out_questions.first())

    def test_user_answer_question(self):
        '''
        test 5 cases:
            [1] user must be logged in
            [2] username in the uri must be the same for the logged in user
            [3] invalid question id
            [4] 1 <= answer's length <= 500
            [5] question is already answered
        '''
        fake = Faker()
        Role.populate_table()
        User.generate_fake_users(count=2)
        testuser1, testuser2 = User.query.get(1), User.query.get(2)
        testuser1.password = '123'
        User.generate_fake_questions(testuser1.username, count=1)
        test_question = testuser1.in_questions.first()

        with self.app.test_request_context():
            with self.app.test_client() as app_test_client:
                #case [1]
                response = app_test_client.get(url_for('main.user_answer_question', 
                                                       username=testuser1.username,
                                                       question_id=test_question.id),
                                               follow_redirects=True)
                self.assertTrue('testing-signin-AMA' in response.get_data(as_text=True))

                app_test_client.post(url_for('auth.signin'), data={'username': testuser1.username,
                                                                   'password': '123'})
                
                response = app_test_client.get(url_for('main.user_answer_question',
                                                       username=testuser1.username,
                                                       question_id=test_question.id))
                self.assertTrue('testing-answer-question-form-AMA' in response.get_data(as_text=True))

                #case [2]
                response = app_test_client.get(url_for('main.user_answer_question', 
                                                       username=testuser2.username, 
                                                       question_id=test_question.id),
                                               follow_redirects=True)
                self.assertTrue('testing-home-AMA' in response.get_data(as_text=True))

                #case [3]
                response = app_test_client.get(url_for('main.user_answer_question', 
                                                       username=testuser1.username, 
                                                       question_id=fake.random_number(digits=4)),
                                               follow_redirects=True)
                self.assertEqual(response.status_code, NotFound.code)

                #case [4]
                answer_content_void = ''
                answer_content_long = fake.sentence(nb_words=600, 
                                                    variable_nb_words=True, ext_word_list=None)
                answer_content_short = fake.sentence(nb_words=40, 
                                                     variable_nb_words=True, ext_word_list=None)
                
                response = app_test_client.post(url_for('main.user_answer_question',
                                                        username=testuser1.username, 
                                                        question_id=test_question.id),
                                                data={'answer': answer_content_void},
                                                follow_redirects=True)
                self.assertTrue('testing-answer-question-form-AMA' in response.get_data(as_text=True))

                response = app_test_client.post(url_for('main.user_answer_question',
                                                        username=testuser1.username, 
                                                        question_id=test_question.id),
                                                data={'answer': answer_content_long},
                                                follow_redirects=True)
                self.assertTrue('testing-answer-question-form-AMA' in response.get_data(as_text=True))                

                response = app_test_client.post(url_for('main.user_answer_question',
                                                        username=testuser1.username, 
                                                        question_id=test_question.id),
                                                data={'answer': answer_content_short},
                                                follow_redirects=True)
                self.assertTrue('testing-user-profile-AMA' in response.get_data(as_text=True))

                #case [5]
                response = app_test_client.post(url_for('main.user_answer_question',
                                                        username=testuser1.username, 
                                                        question_id=test_question.id),
                                                data={'answer': answer_content_short},
                                                follow_redirects=True)
                self.assertTrue('testing-home-AMA' in response.get_data(as_text=True))

    def test_follow_user(self):
        '''
        test 4 cases:
            [1] user is logged in and has the permissions to follow/unfollow other users
            [2] no user exists with the username in the requested uri
            [3] user can't request follow himself
            [4] the logged in user is already following that user 
        '''
        Role.populate_table()
        user_role = Role.query.filter(Role.role_name == 'user').first()
        fake = Faker()
        testuser1 = User(username=fake.user_name(), role=user_role, account_confirmed=True,
                         email=fake.safe_email())
        testuser2 = User(username=fake.user_name(), role=user_role, account_confirmed=True,
                         email=fake.safe_email())
        testuser1.password = '123'
        app_database.session.add_all([testuser1, testuser2])
        app_database.session.commit()

        with self.app.test_request_context():
            with self.app.test_client() as app_test_client:
                #case 1
                response = app_test_client.get(url_for('main.follow_user', 
                                                       username=testuser2.username),
                                               follow_redirects=True)
                self.assertTrue('testing-signin-AMA' in response.get_data(as_text=True))

                app_test_client.post(url_for('auth.signin'), data={
                    'username': testuser1.username,
                    'password': '123'})
                
                response = app_test_client.get(url_for('main.follow_user',
                                                       username=testuser2.username), 
                                               follow_redirects=True)
                self.assertTrue('testing-user-profile-AMA' in response.get_data(as_text=True))
                self.assertEqual(testuser1.follows.count(), 1)

                testuser1.role.permissions &= ~AppPermissions.FOLLOW_OTHERS
                response = app_test_client.get(url_for('main.follow_user',
                                                       username=testuser2.username))
                self.assertEqual(response.status_code, Forbidden.code)
                testuser1.role.permissions = Role.roles['user']

                #case [2]
                response = app_test_client.get(url_for('main.follow_user', 
                                                       username=fake.user_name()))
                self.assertEqual(response.status_code, NotFound.code)

                #case [3]
                response = app_test_client.get(url_for('main.follow_user',
                                                       username=testuser1.username),
                                               follow_redirects=True)
                self.assertTrue('testing-home-AMA' in response.get_data(as_text=True))

                #case [4]
                response = app_test_client.get(url_for('main.follow_user',
                                                       username=testuser2.username),
                                               follow_redirects=True)
                self.assertTrue('testing-home-AMA' in response.get_data(as_text=True))

    def test_unfollow_user(self):
        '''
        test 4 cases:
            [1] user is logged in and has the permissions to follow/unfollow other users
            [2] no user exists with the username in the uri
            [3] user can't unfollow himself
            [4] the logged in user is not following that user
        '''
        Role.populate_table()
        fake = Faker()
        user_role = Role.query.filter(Role.role_name == 'user').first()
        testuser1 = User(username=fake.user_name(), role=user_role, account_confirmed=True,
                         email=fake.safe_email())
        testuser2 = User(username=fake.user_name(), role=user_role, account_confirmed=True,
                         email=fake.safe_email())
        testuser1.password = '123'
        app_database.session.add_all([testuser1, testuser2])
        app_database.session.commit()
        testuser1.follow(testuser2)
        app_database.session.commit()

        with self.app.test_request_context():
            with self.app.test_client() as app_test_client:
                #case [1]
                response = app_test_client.get(url_for('main.unfollow_user', 
                                                       username=testuser2.username), 
                                               follow_redirects=True)
                self.assertTrue('testing-signin-AMA' in response.get_data(as_text=True))

                app_test_client.post(url_for('auth.signin'), data={
                    'username': testuser1.username,
                    'password': '123'})

                testuser1.role.permissions &= ~AppPermissions.FOLLOW_OTHERS
                response = app_test_client.get(url_for('main.unfollow_user', 
                                                       username=testuser2.username))
                self.assertEqual(response.status_code, Forbidden.code)
                testuser1.role.permissions = Role.roles['user']

                response = app_test_client.get(url_for('main.unfollow_user', 
                                                       username=testuser2.username), 
                                               follow_redirects=True)
                self.assertTrue('testing-user-profile-AMA' in response.get_data(as_text=True))
                self.assertEqual(testuser1.follows.count(), 0)
                self.assertEqual(testuser2.followed_by.count(), 0)

                #case [2]
                response = app_test_client.get(url_for('main.unfollow_user', 
                                                       username=fake.user_name()))
                self.assertEqual(response.status_code, NotFound.code)

                #case [3]
                response = app_test_client.get(url_for('main.unfollow_user', 
                                                       username=testuser1.username), 
                                               follow_redirects=True)
                self.assertTrue('testing-home-AMA' in response.get_data(as_text=True))

                #case [4]
                response = app_test_client.get(url_for('main.unfollow_user',
                                                       username=testuser2.username), 
                                               follow_redirects=True)
                self.assertTrue('testing-home-AMA' in response.get_data(as_text=True))


                
