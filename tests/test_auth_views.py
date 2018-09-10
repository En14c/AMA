import unittest, time, os, hashlib
from itsdangerous import TimedJSONWebSignatureSerializer
from flask import url_for
from app import create_app, app_database
from app.models import User
from confg import app_config, TokenExpirationTime


class TestAuthViews(unittest.TestCase):
    def setUp(self):
        self.app = create_app(app_config['testing'])
        self.app_ctx = self.app.app_context()
        self.app_ctx.push()
        app_database.create_all()

    def tearDown(self):
        app_database.session.remove()
        app_database.drop_all()
        self.app_ctx.pop()
    
    def test_signin(self):
        """
        test :
            - logging users in and redirecting to home page
            - next query * if present * does not redirect to external websites
        """
        testuser = User(username='testuser', account_confirmed=True)
        testuser.password = '123'
        app_database.session.add(testuser)
        app_database.session.commit()
        with self.app.test_request_context():
            with self.app.test_client() as app_test_client:
                '''user sign in - gets redirected to home page - url parameter (next) is not set'''
                response = app_test_client.post(url_for('auth.signin'), data={
                    'username' : 'testuser', 'password' : '123'}, follow_redirects=True)
                self.assertTrue('testing-home-AMA' in response.get_data(as_text=True))

                '''user is already signed in - gets redirected to home page'''
                response = app_test_client.get(url_for('auth.signin'), follow_redirects=True)
                self.assertTrue('testing-home-AMA' in response.get_data(as_text=True))
            
            with self.app.test_client() as app_test_client:
                '''user sign in - gets redirected to home page - url parameter (next) is set to external website'''
                response = app_test_client.post(url_for('auth.signin', next='https://www.google.com'),
                    data={'username' : 'testuser', 'password' : '123'}, follow_redirects=True)
                self.assertTrue('testing-home-AMA' in response.get_data(as_text=True))
            
            with self.app.test_client() as app_test_client:
                '''user sign in - gets redirected to the relative path stored in the url parameter (next)'''
                response = app_test_client.post(url_for('auth.signin', next='/'), data={
                    'username' : 'testuser', 'password' : '123'}, follow_redirects=True)
                self.assertTrue('testing-home-AMA' in response.get_data(as_text=True))

    def test_signout(self):
        """ user sign out and gets redirected to sign in page """
        testuser = User(username='testuser')
        testuser.password = '123'
        app_database.session.add(testuser)
        app_database.session.commit()
        with self.app.test_request_context():
            with self.app.test_client() as app_test_client:
                ''' logging user in '''
                app_test_client.post(url_for('auth.signin'), data={
                    'username' : 'testuser', 'password' : '123'}, follow_redirects=True)

                response = app_test_client.get(url_for('auth.signout'), follow_redirects=True)
                self.assertTrue('testing-signin-AMA' in response.get_data(as_text=True))

    def test_signup(self):
        """ add user to the database and redirect him to login page """
        testuser0 = User(username='testuser0')
        testuser0.password = '123'
        app_database.session.add(testuser0)
        app_database.session.commit()

        with self.app.test_request_context():
            with self.app.test_client() as app_test_client:
                app_test_client.post(url_for('auth.signin'), data={'username':'testuser0',
                                                                   'password':'123'})
                response = app_test_client.get(url_for('auth.signup'))
                self.assertTrue(response.status_code == 302)
                app_test_client.get(url_for('auth.signout'))

                resposne = app_test_client.get(url_for('auth.signup'))
                self.assertTrue('testing-signup-AMA' in resposne.get_data(as_text=True))

                resposne = app_test_client.post(url_for('auth.signup'), data={
                        'username': 'testuser', 'password': '123', 'email': 'testuser@mail.com'},
                        follow_redirects=True)
                self.assertTrue('testing-signin-AMA' in resposne.get_data(as_text=True))

                ''' user added to the database ?'''
                test_user = User.query.get(1)
                self.assertIsNotNone(test_user)

    def test_confirm_account(self):
        '''
        test 3 cases:
            [1] account already confirmed
            [2] confirmation link is valid
            [3] confirmation link is invalid or has expired
        '''
        testuser = User(username='testuser', email=self.app.config['MAIL_SENDER'],
                        account_confirmed=True)
        testuser.password = '123'
        app_database.session.add(testuser)
        app_database.session.commit()

        with self.app.test_request_context():
            with self.app.test_client() as app_test_client:
                #login 
                app_test_client.post(url_for('auth.signin'), data={'username': 'testuser',
                                                                   'password': '123'})
                
                #case [1]
                token = testuser.create_confirmation_token(exp=TokenExpirationTime.AFTER_0_MIN)
                response = app_test_client.get(url_for('auth.confirm_account', confirmation_token=token), 
                                               follow_redirects=True)
                self.assertTrue('testing-home-AMA' in response.get_data(as_text=True))

                #case [2]
                testuser.account_confirmed = False
                token = testuser.create_confirmation_token(exp=TokenExpirationTime.AFTER_5_MIN)
                response = app_test_client.get(url_for('auth.confirm_account', confirmation_token=token), 
                                               follow_redirects=True)
                self.assertTrue('testing-home-AMA' in response.get_data(as_text=True))

                #case [3]
                testuser.account_confirmed = False
                token = testuser.create_confirmation_token(exp=TokenExpirationTime.AFTER_0_MIN)
                time.sleep(2)
                response = app_test_client.get(url_for('auth.confirm_account', confirmation_token=token),
                                               follow_redirects=True)
                self.assertTrue('testing-accountConfirmation-AMA' in response.get_data(as_text=True))

    def test_change_password(self):
        """
        test 2 cases:
            - incorrect current password submitted
            - correct current password submitted
        """
        testuser = User(username='testuser', email=self.app.config['MAIL_SENDER'],
                        account_confirmed=True)
        testuser.password = '123'
        app_database.session.add(testuser)
        app_database.session.commit()

        with self.app.test_request_context():
            with self.app.test_client() as app_test_client:
                #login
                app_test_client.post(url_for('auth.signin'), data={'username': 'testuser',
                                                                   'password': 123})

                #case [1]
                response = app_test_client.post(url_for('auth.change_password'), data={
                    'current_password': '321', 'new_password': '1234'}, follow_redirects=True)
                self.assertFalse('testing-home-AMA' in response.get_data(as_text=True))

                #case [2]
                response = app_test_client.post(url_for('auth.change_password'), data={
                    'current_password': '123', 'new_password': '1234'}, follow_redirects=True)
                self.assertTrue('testing-home-AMA' in response.get_data(as_text=True))
                self.assertTrue(testuser.check_password('1234'))
            
    def test_confirm_email_address(self):
        """
        test 2 cases:
            [1] email address confirmation expired or invalid
            [2] email address confirmation is valid and user's email address is updated
        """
        testuser = User(username='testuser', email=self.app.config['MAIL_SENDER'],
                        account_confirmed=True)
        testuser.password = '123'
        app_database.session.add(testuser)
        app_database.session.commit()
        token_payload = {'new_email': 'test@mail.com'}

        with self.app.test_request_context():
            with self.app.test_client() as app_test_client:
                #login
                app_test_client.post(url_for('auth.signin'), data={'username': 'testuser',
                                                                   'password': '123'})

                #case [1]
                serializer = TimedJSONWebSignatureSerializer(self.app.config['SECRET_KEY'], 
                                                             expires_in=TokenExpirationTime.AFTER_0_MIN)
                token = serializer.dumps(token_payload)
                time.sleep(2)
                response = app_test_client.get(url_for('auth.confirm_new_email_address', 
                                                                confirmation_token=token))
                self.assertTrue(response.status_code == 302)
                self.assertFalse(testuser.email == token_payload['new_email'])

                #case [2]
                serializer = TimedJSONWebSignatureSerializer(self.app.config['SECRET_KEY'], 
                                                             expires_in=TokenExpirationTime.AFTER_5_MIN)
                token = serializer.dumps(token_payload)
                response = app_test_client.get(url_for('auth.confirm_new_email_address',
                                                                confirmation_token=token))
                self.assertTrue(response.status_code == 302)
                self.assertTrue(testuser.email == token_payload['new_email'])

  
    def test_password_reset_init(self):
        '''
        test 3 cases:
            [1] user is not logged in => requests the [ /passwordreset ] link => display a form
            [2] user is not logged in a submits the form => continue the password reset process
            [3] user is logged in => requests the [ /passwordreset ] link => gets redirected to home page
        '''
        testuser = User(username='testuser', email=self.app.config['MAIL_SENDER'], 
                        account_confirmed=True)
        testuser.password = '123'
        app_database.session.add(testuser)
        app_database.session.commit()

        with self.app.test_request_context():
            with self.app.test_client() as app_test_client:
                #case [1]
                response = app_test_client.get(url_for('auth.password_reset_init'))
                self.assertTrue('testing-password-reset-init-AMA' in response.get_data(as_text=True))

                #case [2]
                response = app_test_client.post(url_for('auth.password_reset_init'))
                self.assertTrue(response.status_code == 302)

                #case [3]
                app_test_client.post(url_for('auth.signin'), data={
                            'username': 'testuser', 'password': '123'})
                response = app_test_client.get(url_for('auth.password_reset_init'), follow_redirects=True)
                self.assertTrue('testing-home-AMA' in response.get_data(as_text=True))

    def test_password_reset_request(self):
        '''
        test 3 cases:
            [1] the password reset request link is malformed
            [2] the password reset request link is valid and user submits the form with registered email address
            [3] the password reset request link is valid but use submits the form with unregistered email address
        '''
        testuser = User(email=self.app.config['MAIL_SENDER'])
        app_database.session.add(testuser)
        app_database.session.commit()

        with self.app.test_request_context():
            with self.app.test_client() as app_test_client:
                #case [1]
                serializer = TimedJSONWebSignatureSerializer(str(os.urandom(2)), 
                                                             expires_in=TokenExpirationTime.AFTER_5_MIN)
                token = serializer.dumps(str(os.urandom(2)))
                response = app_test_client.get(url_for('auth.password_reset_request', token=token))
                self.assertTrue(response.status_code == 404)

                #case [2]
                response = app_test_client.post(url_for('auth.password_reset_init'))
                response = app_test_client.post(response.location, data={'email':testuser.email})
                self.assertTrue(response.status_code == 302)

                #case [3]
                response = app_test_client.post(url_for('auth.password_reset_init'))
                response = app_test_client.post(response.location, data={'email':'test@mail.com'})
                self.assertTrue('testing-password-reset-request-AMA' in response.get_data(as_text=True))

    def test_password_reset_confirm(self):
        '''
        test [4] cases:
            [1] password reset request didn't come from the password reset request email
            [2] invalid or malformed password reset confirmation link
            [3] expired password reset confirmation link
            [4] valid confirmation link and comes from a password request email => update user password
        '''
        testuser = User(email=self.app.config['MAIL_SENDER'])
        testuser.password = '123'
        app_database.session.add(testuser)
        app_database.session.commit()

        with self.app.test_request_context():
            with self.app.test_client() as app_test_client:
                #case [1]
                serializer = TimedJSONWebSignatureSerializer(self.app.config['SECRET_KEY'], 
                                                             expires_in=TokenExpirationTime.AFTER_5_MIN)
                token_payload = {'email':'test@mail.com'}
                token = serializer.dumps(token_payload)
                response = app_test_client.get(url_for('auth.password_reset_confirm', 
                                                       confirmation_token=token))
                self.assertTrue(response.status_code == 404)

                #case [2]
                with app_test_client.session_transaction() as session_trans:
                    session_trans['password-reset-request'] = hashlib.md5(os.urandom(2)).hexdigest()
                serializer = TimedJSONWebSignatureSerializer(str(os.urandom(2)), 
                                                             expires_in=TokenExpirationTime.AFTER_5_MIN)
                token_payload = {'email':'test@mail.com'}
                token = serializer.dumps(token_payload)
                response = app_test_client.get(url_for('auth.password_reset_confirm', 
                                                       confirmation_token=token))
                self.assertTrue(response.status_code == 302)

                #case [3]
                with app_test_client.session_transaction() as session_trans:
                    session_trans['password-reset-request'] = hashlib.md5(os.urandom(2)).hexdigest()
                serializer = TimedJSONWebSignatureSerializer(self.app.config['SECRET_KEY'], 
                                                             expires_in=TokenExpirationTime.AFTER_0_MIN)
                token_payload = {'email':'test@mail.com'}
                token = serializer.dumps(token_payload)
                time.sleep(5)
                response = app_test_client.get(url_for('auth.password_reset_confirm', 
                                                       confirmation_token=token))
                self.assertTrue(response.status_code == 302)                
                
                #case [4]
                with app_test_client.session_transaction() as session_trans:
                    session_trans['password-reset-request'] = hashlib.md5(os.urandom(2)).hexdigest()
                serializer = TimedJSONWebSignatureSerializer(self.app.config['SECRET_KEY'], 
                                                             expires_in=TokenExpirationTime.AFTER_5_MIN)
                token_payload = {'email':testuser.email}
                token = serializer.dumps(token_payload)
                app_test_client.post(url_for('auth.password_reset_confirm',
                                             confirmation_token=token), data={'password':'1234'})
                self.assertTrue(testuser.check_password('1234'))
                