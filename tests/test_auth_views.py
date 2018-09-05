import unittest, time
from flask import url_for
from app import create_app, app_database
from app.models import User
from confg import app_config


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
        with self.app.test_request_context():
            with self.app.test_client() as app_test_client:
                ''' get the signup page '''
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
                token = testuser.create_confirmation_token(exp=0)
                response = app_test_client.get(url_for('auth.confirm_account', confirmation_token=token), 
                                               follow_redirects=True)
                self.assertTrue('testing-home-AMA' in response.get_data(as_text=True))

                #case [2]
                testuser.account_confirmed = False
                token = testuser.create_confirmation_token(exp=180)
                response = app_test_client.get(url_for('auth.confirm_account', confirmation_token=token), 
                                               follow_redirects=True)
                self.assertTrue('testing-home-AMA' in response.get_data(as_text=True))

                #case [3]
                testuser.account_confirmed = False
                token = testuser.create_confirmation_token(exp=0)
                time.sleep(2)
                response = app_test_client.get(url_for('auth.confirm_account', confirmation_token=token),
                                               follow_redirects=True)
                self.assertTrue('testing-accountConfirmation-AMA' in response.get_data(as_text=True))