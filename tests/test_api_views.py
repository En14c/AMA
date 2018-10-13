import unittest, base64, time, random
from itsdangerous import TimedJSONWebSignatureSerializer
from flask import url_for
from werkzeug.exceptions import Unauthorized, Forbidden, NotFound
from faker import Faker
from app import create_app, app_database
from app.models import User, Role, TokenExpirationTime
from confg import app_config



class TestAPI(unittest.TestCase):
    def setUp(self):
        self.app = create_app(app_config['testing'])
        self.app_ctx = self.app.app_context()
        self.app_ctx.push()
        app_database.create_all()

    def tearDown(self):
        app_database.session.remove()
        app_database.drop_all()
        self.app_ctx.pop()

    def api_request_headers_basic_auth(self, username, password):
        return {
            'Authorization': 'Basic ' +
                             base64.b64encode((username + ':' + password).encode('utf-8')).decode('utf-8'),
            'Content-type': 'application/json',
            'Accept': 'application/json'
        }

    def api_request_headers_bearer_auth(self, auth_token):
        return {
            'Authorization': 'Bearer ' + auth_token,
            'Content-type': 'application/json',
            'Accept': 'application/json'
        }
    
    def test_api_verify_username_password(self):
        '''
        test 3 cases:
            - valid username and invalid password
            - invalid username
                +
                +----> response -> unauthorized
            - valid username and password
                +
                +----> response -> json response of the requested url
        '''
        fake = Faker()
        Role.populate_table()
        user_role = Role.load_role_by_name(role_name='user')
        testuser = User(username=fake.user_name(), email=fake.safe_email(), role=user_role)
        testuser.password = '123'
        app_database.session.add(testuser)
        app_database.session.commit()

        with self.app.test_request_context():
            with self.app.test_client(use_cookies=False) as app_test_client:
                request_headers = self.api_request_headers_basic_auth(username=testuser.username, 
                                                                      password=fake.password())
                response = app_test_client.get(url_for('api.api_get_user_profile_info', username=testuser.username), 
                                               headers=request_headers)
                self.assertEqual(response.status_code, Unauthorized.code)

                request_headers = self.api_request_headers_basic_auth(username=fake.user_name(), password='123')
                response = app_test_client.get(url_for('api.api_get_user_profile_info', username=testuser.username), 
                                               headers=request_headers)
                self.assertEqual(response.status_code, Unauthorized.code)

                request_headers = self.api_request_headers_basic_auth(username=testuser.username, password='123')
                response = app_test_client.get(url_for('api.api_get_user_profile_info', username=testuser.username),
                                               headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertIsNotNone(response_data)
                self.assertIsNotNone(response_data.get('status_code'))
                self.assertEqual(response_data.get('status_code'), 200)

    def test_api_generate_auth_token(self):
        '''
        test 2 cases:
            [1] user requests authentication token for the first time
                +
                +--> respond -> json data -> {'auth_token': token, ...}
            [2] user requests authentication token whilst he already has one that has not expired yet
        '''
        fake = Faker()
        testuser = User(username=fake.user_name(), email=fake.safe_email())
        testuser.password = '123'
        app_database.session.add(testuser)
        app_database.session.commit()
        request_headers = self.api_request_headers_basic_auth(username=testuser.username, password='123')

        with self.app.test_request_context():
            with self.app.test_client(use_cookies=False) as app_test_client:
                # case[1]
                response = app_test_client.get(url_for('api.api_generate_auth_token'), headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertNotEqual(response.status_code, Unauthorized.code)
                self.assertIsNotNone(response_data)
                self.assertIsNotNone(response_data.get('auth_token'))
                self.assertIsNotNone(testuser.api_auth_token)
                self.assertEqual(testuser.api_auth_token, response_data.get('auth_token'))
                self.assertIsNotNone(User.api_verify_auth_token(testuser.api_auth_token))

                # case[2]
                response = app_test_client.get(url_for('api.api_generate_auth_token'), headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertIsNotNone(response_data)
                self.assertEqual(response_data.get('status_code'), Forbidden.code)
    
    def test_api_verify_token(self):
        '''
        test 3 cases:
            [1] authentication token is invalid
            [2] authentication token is valid 
            [3] authentication token is valid but no user exist with the provided id
        '''
        fake = Faker()
        Role.populate_table()
        user_role = Role.load_role_by_name(role_name='user')
        testuser = User(username=fake.user_name(), email=fake.safe_email(), role=user_role)
        app_database.session.add(testuser)
        app_database.session.commit()

        with self.app.test_request_context():
            with self.app.test_client(use_cookies=False) as app_test_client:
                # case[1]
                testuser.api_generate_auth_token(expires_in=TokenExpirationTime.AFTER_0_MIN)
                request_headers = self.api_request_headers_bearer_auth(testuser.api_auth_token)
                time.sleep(3)
                response = app_test_client.get(url_for('api.api_get_users_list', n=1), headers=request_headers)
                self.assertEqual(response.status_code, Unauthorized.code)
                
                #case [2]
                testuser.api_generate_auth_token()
                request_headers = self.api_request_headers_bearer_auth(testuser.api_auth_token)
                response = app_test_client.get(url_for('api.api_get_users_list', n=1), headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertNotEqual(response.status_code, Unauthorized.code)
                self.assertIsNotNone(response_data)
                self.assertIsNotNone(response_data.get('status_code'))
                self.assertEqual(response_data.get('status_code'), 200)

                # case[3]
                auth_token_gen = TimedJSONWebSignatureSerializer(self.app.config['SECRET_KEY'],
                                                                 expires_in=TokenExpirationTime.AFTER_15_MIN)
                auth_token = auth_token_gen.dumps({'auth_token_id': fake.random_int()})
                request_headers = self.api_request_headers_bearer_auth(auth_token.decode())
                response = app_test_client.get(url_for('api.api_get_users_list', n=1), headers=request_headers)
                self.assertEqual(response.status_code, Unauthorized.code)
               
    def test_api_get_user_profile_info(self):
        '''
        test 3 cases:
            [1] authorization required
            [2] valid authorization and the requested username is valid
            [3] valid authorization and the requested username is invalid       
        '''
        fake = Faker()
        Role.populate_table()
        user_role = Role.load_role_by_name(role_name='user')
        User.generate_fake_users()
        testuser = User(username=fake.user_name(), email=fake.safe_email(), account_confirmed=True,
                        role=user_role, about_me=fake.sentence(nb_words=10))
        testuser.generate_gravatar_uri()
        app_database.session.add(testuser)
        app_database.session.commit()
        User.generate_fake_followers(testuser.username)
        User.generate_fake_followed_users(testuser.username)
        testuser.api_generate_auth_token()
        request_headers = self.api_request_headers_bearer_auth(testuser.api_auth_token)

        with self.app.test_request_context():
            with self.app.test_client(use_cookies=False) as app_test_client:
                # case[1]
                response = app_test_client.get(url_for('api.api_get_user_profile_info', username=testuser.username),
                    headers=self.api_request_headers_bearer_auth(testuser.api_auth_token + str(fake.random_int())))
                self.assertEqual(response.status_code, Unauthorized.code)
                response = app_test_client.get(url_for('api.api_get_user_profile_info', username=testuser.username),
                                               headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertIsNotNone(response_data)
                self.assertEqual(response_data.get('status_code'), 200)

                # case[2]
                response = app_test_client.get(url_for('api.api_get_user_profile_info', username=testuser.username), 
                                               headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertNotEqual(response.status_code, Unauthorized.code)
                self.assertIsNotNone(response_data)
                self.assertEqual(response_data.get('status_code'), 200)
                self.assertEqual(response_data.get('id'), testuser.id)
                self.assertEqual(response_data.get('username'), testuser.username)
                self.assertEqual(response_data.get('about_me'), testuser.about_me)
                self.assertEqual(response_data.get('avatar_uri'), testuser.generate_gravatar_uri())
                self.assertEqual(response_data.get('#followers'), testuser.followed_by.count())
                self.assertEqual(response_data.get('#following'), testuser.follows.count())
                self.assertEqual(response_data.get('followers'), 
                                 url_for('api.api_get_followers_list', username=testuser.username, p=1,
                                         _external=True))
                self.assertEqual(response_data.get('following'), 
                                 url_for('api.api_get_followed_users_list', username=testuser.username, p=1, 
                                         _external=True))
                self.assertEqual(response_data.get('account_confirmed'), True)
                self.assertEqual(response_data.get('role'), testuser.role.role_name)

                # case[3]
                response = app_test_client.get(url_for('api.api_get_user_profile_info', username=fake.user_name()),
                                               headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertIsNotNone(response_data)
                self.assertEqual(response_data.get('status_code'), NotFound.code)


    def test_api_get_users_list(self):
        '''
        test 2 cases:
            [1] authorization required
            [2] list of of informations about each user is returned. the link to get the next (n) users is followed like 
                a linked list until (NULL) is found
        '''
        fake = Faker()
        Role.populate_table()
        user_role = Role.load_role_by_name(role_name='user')
        User.generate_fake_users()
        testuser = User(username=fake.user_name(), email=fake.safe_email(), role=user_role)
        app_database.session.add(testuser)
        app_database.session.commit()
        User.generate_fake_followers(testuser.username)
        User.generate_fake_followed_users(testuser.username)
        testuser.api_generate_auth_token()
        request_headers = self.api_request_headers_bearer_auth(testuser.api_auth_token)

        with self.app.test_request_context():
            with self.app.test_client(use_cookies=False) as app_test_client:
                # case[1]
                response = app_test_client.get(url_for('api.api_get_users_list'),
                    headers=self.api_request_headers_bearer_auth(testuser.api_auth_token + str(fake.random_int())))
                self.assertEqual(response.status_code, Unauthorized.code)
                response = app_test_client.get(url_for('api.api_get_users_list'), headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertIsNotNone(response_data)
                self.assertEqual(response_data.get('status_code'), 200)

                #case [2]
                response = app_test_client.get(url_for('api.api_get_users_list', n=1), headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertIsNotNone(response_data)
                self.assertIsNotNone(response_data.get('next'))
                while response_data.get('next') != 'NULL':
                    self.assertIsNotNone(response_data.get('users'))
                    self.assertEqual(len(response_data.get('users')), 1)
                    self.assertIsNotNone(response_data.get('users')[0].get('status_code'), 200)
                    self.assertIsNotNone(response_data.get('users')[0].get('id'))
                    self.assertIsNotNone(response_data.get('users')[0].get('username'))
                    self.assertIsNotNone(response_data.get('users')[0].get('about_me'))
                    self.assertIsNotNone(response_data.get('users')[0].get('#followers'))
                    self.assertIsNotNone(response_data.get('users')[0].get('#following'))
                    self.assertIsNotNone(response_data.get('users')[0].get('followers'))
                    self.assertIsNotNone(response_data.get('users')[0].get('following'))
                    self.assertIsNotNone(response_data.get('users')[0].get('account_confirmed'), True)
                    self.assertIsNotNone(response_data.get('users')[0].get('role'), testuser.role.role_name)
                    response = app_test_client.get(response_data.get('next'), headers=request_headers)
                    response_data = response.get_json(silent=True, cache=False)
                    self.assertIsNotNone(response_data)   

    def test_api_get_followers_list(self):
        '''
        test 3 cases:
            [1] authorization required
            [2] request to get followers of (invalid/non-registered) username
            [3] a list of informations about each follower of the requested username is returned. the link to get the next (n)
                followers is followed unitl a (NULL) is found
        '''
        fake = Faker()
        Role.populate_table()
        user_role = Role.load_role_by_name(role_name='user')
        User.generate_fake_users()
        testuser = User(username=fake.user_name(), email=fake.safe_email(), role=user_role)
        app_database.session.add(testuser)
        app_database.session.commit()
        User.generate_fake_followers(testuser.username)
        User.generate_fake_followed_users(testuser.username)
        testuser.api_generate_auth_token()
        request_headers = self.api_request_headers_bearer_auth(testuser.api_auth_token)

        with self.app.test_request_context():
            with self.app.test_client(use_cookies=False) as app_test_client:
                #case [1]
                response = app_test_client.get(url_for('api.api_get_followers_list', username=testuser.username),
                    headers=self.api_request_headers_bearer_auth(testuser.api_auth_token + str(fake.random_int())))
                self.assertEqual(response.status_code, Unauthorized.code)
                response = app_test_client.get(url_for('api.api_get_followers_list', username=testuser.username),
                                               headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertIsNotNone(response_data)
                self.assertEqual(response_data.get('status_code'), 200)

                #case [2]
                response = app_test_client.get(url_for('api.api_get_followers_list', username=fake.user_name()),
                                               headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertIsNotNone(response_data)
                self.assertEqual(response_data.get('status_code'), NotFound.code)
                response = app_test_client.get(url_for('api.api_get_followers_list', username=testuser.username),
                                               headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertIsNotNone(response_data)
                self.assertEqual(response_data.get('status_code'), 200)

                #case [3]
                response = app_test_client.get(url_for('api.api_get_followers_list', username=testuser.username, n=1),
                                               headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertIsNotNone(response_data)
                self.assertIsNotNone(response_data.get('next'))
                while response_data.get('next') != 'NULL':
                    self.assertIsNotNone(response_data.get('followers'))
                    self.assertIsNotNone(response_data.get('followers')[0].get('status_code'))
                    self.assertIsNotNone(response_data.get('followers')[0].get('id'))
                    self.assertIsNotNone(response_data.get('followers')[0].get('username'))
                    self.assertIsNotNone(response_data.get('followers')[0].get('about_me'))
                    self.assertIsNotNone(response_data.get('followers')[0].get('avatar_uri'))
                    self.assertIsNotNone(response_data.get('followers')[0].get('#followers'))
                    self.assertIsNotNone(response_data.get('followers')[0].get('#following'))
                    self.assertIsNotNone(response_data.get('followers')[0].get('followers'))
                    self.assertIsNotNone(response_data.get('followers')[0].get('following'))
                    self.assertIsNotNone(response_data.get('followers')[0].get('account_confirmed'))
                    self.assertIsNotNone(response_data.get('followers')[0].get('role'))
                    response = app_test_client.get(response_data.get('next'), headers=request_headers)
                    response_data = response.get_json(silent=True, cache=False)
                    self.assertIsNotNone(response_data)

    def test_api_get_followed_users_list(self):
        '''
        test 3 cases:
            [1] authorization required
            [2] request to get users followed by (invalid/non-registered) username
            [3] a list of the users followed by the requested user is returned. the link to get the next (n) followed users is
                followed until (NULL) is found
        '''
        fake = Faker()
        Role.populate_table()
        user_role = Role.load_role_by_name(role_name='user')
        User.generate_fake_users()
        testuser = User(username=fake.user_name(), email=fake.safe_email(), role=user_role)
        app_database.session.add(testuser)
        app_database.session.commit()
        User.generate_fake_followers(testuser.username)
        User.generate_fake_followed_users(testuser.username)
        testuser.api_generate_auth_token()
        request_headers = self.api_request_headers_bearer_auth(testuser.api_auth_token)

        with self.app.test_request_context():
            with self.app.test_client(use_cookies=False) as app_test_client:
                #case [1]
                response = app_test_client.get(url_for('api.api_get_followed_users_list', username=testuser.username),
                    headers=self.api_request_headers_bearer_auth(testuser.api_auth_token + str(fake.random_int())))
                self.assertEqual(response.status_code, Unauthorized.code)
                response = app_test_client.get(url_for('api.api_get_followed_users_list', username=testuser.username),
                                               headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertIsNotNone(response_data)
                self.assertEqual(response_data.get('status_code'), 200)

                #case [2]
                response = app_test_client.get(url_for('api.api_get_followed_users_list', username=fake.user_name()),
                                               headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertIsNotNone(response_data)
                self.assertEqual(response_data.get('status_code'), NotFound.code)
                response = app_test_client.get(url_for('api.api_get_followed_users_list', username=testuser.username),
                                               headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertIsNotNone(response_data)
                self.assertEqual(response_data.get('status_code'), 200)

                #case [3]
                response = app_test_client.get(url_for('api.api_get_followed_users_list', username=testuser.username, n=1),
                                               headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertIsNotNone(response_data)
                self.assertIsNotNone(response_data.get('next'))
                while response_data.get('next') != 'NULL':
                    self.assertIsNotNone(response_data.get('following'))
                    self.assertEqual(response_data.get('following')[0].get('status_code'), 200)
                    self.assertIsNotNone(response_data.get('following')[0].get('id'))
                    self.assertIsNotNone(response_data.get('following')[0].get('username'))
                    self.assertIsNotNone(response_data.get('following')[0].get('about_me'))
                    self.assertIsNotNone(response_data.get('following')[0].get('avatar_uri'))
                    self.assertIsNotNone(response_data.get('following')[0].get('#followers'))
                    self.assertIsNotNone(response_data.get('following')[0].get('#following'))
                    self.assertIsNotNone(response_data.get('following')[0].get('followers'))
                    self.assertIsNotNone(response_data.get('following')[0].get('following'))
                    self.assertIsNotNone(response_data.get('following')[0].get('account_confirmed'))
                    self.assertIsNotNone(response_data.get('following')[0].get('role'))
                    response = app_test_client.get(response_data.get('next'), headers=request_headers)
                    response_data = response.get_json(silent=True, cache=False)
                    self.assertIsNotNone(response_data)
    
    def test_api_get_user_answered_questions(self):
        '''
        test 3 cases:
            [1] authorization required
            [2] request to get answered questions of (invalid/non-registered) username
            [3] a list of informations about questions answered by the username requested. the link to get the next (n) questions
                is followed until (NULL) is found
        '''
        fake = Faker()
        Role.populate_table()
        User.generate_fake_users()
        user_role = Role.load_role_by_name(role_name='user')
        testuser = User(username=fake.user_name(), email=fake.safe_email(), role=user_role)
        app_database.session.add(testuser)
        app_database.session.commit()
        User.generate_fake_questions(testuser.username)
        User.generate_fake_answers(testuser.username)
        testuser.api_generate_auth_token()
        request_headers = self.api_request_headers_bearer_auth(testuser.api_auth_token)

        with self.app.test_request_context():
            with self.app.test_client(use_cookies=False) as app_test_client:
                #case [1]
                response = app_test_client.get(url_for('api.api_get_user_answered_questions', username=testuser.username),
                    headers=self.api_request_headers_bearer_auth(testuser.api_auth_token + str(fake.random_int())))
                self.assertEqual(response.status_code, Unauthorized.code)
                response = app_test_client.get(url_for('api.api_get_user_answered_questions', username=testuser.username),
                                               headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertIsNotNone(response_data)
                self.assertEqual(response_data.get('status_code'), 200)

                #case [2]
                response = app_test_client.get(url_for('api.api_get_user_answered_questions', username=fake.user_name()),
                                               headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertIsNotNone(response_data)
                self.assertEqual(response_data.get('status_code'), NotFound.code)
                response = app_test_client.get(url_for('api.api_get_user_answered_questions', username=testuser.username),
                                               headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertIsNotNone(response_data)
                self.assertEqual(response_data.get('status_code'), 200)

                #case [3]
                response = app_test_client.get(url_for('api.api_get_user_answered_questions', username=testuser.username, n=1),
                                               headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertIsNotNone(response_data)
                self.assertIsNotNone(response_data.get('next'))
                while response_data.get('next') != 'NULL':
                    self.assertIsNotNone(response_data.get('answered_questions'))
                    self.assertIsNotNone(response_data.get('answered_questions')[0].get('status_code'), 200)
                    self.assertIsNotNone(response_data.get('answered_questions')[0].get('asker'))
                    self.assertIsNotNone(response_data.get('answered_questions')[0].get('replier'))
                    self.assertIsNotNone(response_data.get('answered_questions')[0].get('question'))
                    self.assertIsNotNone(response_data.get('answered_questions')[0].get('has_answer'))
                    self.assertIsNotNone(response_data.get('answered_questions')[0].get('answer'))
                    self.assertIsNotNone(response_data.get('answered_questions')[0].get('date'))
                    response = app_test_client.get(response_data.get('next'), headers=request_headers)
                    response_data = response.get_json(silent=True, cache=False)
                    self.assertIsNotNone(response_data)
    
    def test_api_get_user_unanswered_questions(self):
        '''
        test 3 cases:
            [1] authorization required
            [2] request to get unanswered questions of (invalid/non-registered) username
            [3] only the username for whom the unanswered-questions was asked is allowed to get informations about it
            [4] a list of informations about questions answered by the username requested is returned. the link to get the next (n)
                unanswered questions is followed until (NULL) is found 
        '''
        fake = Faker()
        Role.populate_table()
        user_role = Role.load_role_by_name(role_name='user')
        User.generate_fake_users()
        testuser = User(username=fake.user_name(), email=fake.safe_email(), role=user_role)
        app_database.session.add(testuser)
        app_database.session.commit()
        User.generate_fake_questions(testuser.username)
        User.generate_fake_answers(testuser.username)
        testuser.api_generate_auth_token()
        request_headers = self.api_request_headers_bearer_auth(testuser.api_auth_token)

        with self.app.test_request_context():
            with self.app.test_client(use_cookies=False) as app_test_client:
                #case [1]
                response = app_test_client.get(url_for('api.api_get_user_unanswered_questions', username=testuser.username),
                    headers=self.api_request_headers_bearer_auth(testuser.api_auth_token + str(fake.random_int())))
                self.assertEqual(response.status_code, Unauthorized.code)
                response = app_test_client.get(url_for('api.api_get_user_unanswered_questions', username=testuser.username),
                                               headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertIsNotNone(response_data)
                self.assertEqual(response_data.get('status_code'), 200)

                #case [2]
                response = app_test_client.get(url_for('api.api_get_user_unanswered_questions', username=fake.user_name()),
                                               headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertIsNotNone(response_data)
                self.assertEqual(response_data.get('status_code'), NotFound.code)
                response = app_test_client.get(url_for('api.api_get_user_unanswered_questions', username=testuser.username),
                                               headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertIsNotNone(response_data)
                self.assertEqual(response_data.get('status_code'), 200)

                #case [3]
                testuser2 = User.load_user_by_id(random.randint(1, testuser.id - 1))
                response = app_test_client.get(url_for('api.api_get_user_unanswered_questions', username=testuser2.username),
                                               headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertIsNotNone(response_data)
                self.assertEqual(response_data.get('status_code'), Forbidden.code)
                response = app_test_client.get(url_for('api.api_get_user_unanswered_questions', username=testuser.username),
                                               headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertIsNotNone(response_data)
                self.assertEqual(response_data.get('status_code'), 200)

                #case [4]
                response = app_test_client.get(url_for('api.api_get_user_unanswered_questions', username=testuser.username, n=1),
                                               headers=request_headers)
                response_data = response.get_json(silent=True, cache=False)
                self.assertIsNotNone(response_data)
                self.assertIsNotNone(response_data.get('next'))
                while response_data.get('next') != 'NULL':
                    self.assertIsNotNone(response_data.get('unanswered_questions'))
                    self.assertIsNotNone(response_data.get('unanswered_questions')[0].get('status_code'), 200)
                    self.assertIsNotNone(response_data.get('unanswered_questions')[0].get('asker'))
                    self.assertIsNotNone(response_data.get('unanswered_questions')[0].get('replier'))
                    self.assertIsNotNone(response_data.get('unanswered_questions')[0].get('question'))
                    self.assertIsNotNone(response_data.get('unanswered_questions')[0].get('has_answer'))
                    self.assertIsNotNone(response_data.get('unanswered_questions')[0].get('answer'))
                    self.assertIsNotNone(response_data.get('unanswered_questions')[0].get('date'))
                    response = app_test_client.get(response_data.get('next'), headers=request_headers)
                    response_data = response.get_json(silent=True, cache=False)
                    self.assertIsNotNone(response_data)