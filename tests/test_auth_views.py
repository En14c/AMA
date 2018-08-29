import unittest
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
        testuser = User(username='testuser')
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