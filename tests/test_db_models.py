import unittest, time
from app import create_app, app_database
from app.models import User
from confg import app_config, TokenExpirationTime

class TestUserModel(unittest.TestCase):
    def setUp(self):
        self.app = create_app(app_config['testing'])
        self.app_ctx = self.app.app_context()
        self.app_ctx.push()
        app_database.create_all()
    
    def tearDown(self):
        app_database.session.remove()
        app_database.drop_all()
        self.app_ctx.pop()


    def test_password_write_only(self):
        """ test password property is write only """
        user = User()
        user.password = 'testpassword'
        with self.assertRaises(AttributeError):
            user.password
    
    def test_password_hash_salt(self):
        """ test password hash for same passowrd are different """
        user1, user2 = User(), User()
        user1.password = 'testpassword'
        user2.passwrod = 'testpassword'
        self.assertNotEqual(user1.password_hash, user2.password_hash)

    def test_password_verification(self):
        user = User()
        user.password = 'testpassword'
        self.assertFalse(user.check_password('testpassword1234'))
        self.assertTrue(user.check_password('testpassword')) 

    def test_confirmation_token(self):
        """ test valid, invalid or expired confirmation token """
        testuser1 = User()
        app_database.session.add(testuser1)
        app_database.session.commit()

        #test valid confirmation token
        token = testuser1.create_confirmation_token()
        self.assertTrue(testuser1.verify_confirmation_token(token))

        #test invalid confirmation token
        token = testuser1.create_confirmation_token()
        testuser1.id = 2
        self.assertFalse(testuser1.verify_confirmation_token(token))

        #test expired confirmation token
        token = testuser1.create_confirmation_token(exp=TokenExpirationTime.AFTER_0_MIN)
        time.sleep(1)
        self.assertFalse(testuser1.verify_confirmation_token(token))
                