import unittest
from flask import url_for
from app import app_database, create_app
from app.models import User
from confg import app_config



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