import unittest, time
from app import create_app, app_database
from app.models import User, Role, Question, Answer
from confg import app_config, TokenExpirationTime

class TestRoleModel(unittest.TestCase):
    def setUp(self):
        self.app = create_app(app_config['testing'])
        self.app_ctx = self.app.app_context()
        self.app_ctx.push()
        app_database.create_all()

    def tearDown(self):
        app_database.session.remove()
        app_database.drop_all()
        self.app_ctx.pop()

    def test_populate_roles_table(self):
        Role.populate_table()

        user_role = Role.query.filter(Role.role_name == 'user').first()
        admin_role = Role.query.filter(Role.role_name == 'admin').first()

        self.assertIsNotNone(user_role)
        self.assertIsNotNone(admin_role)

class TestQuestionAnswerModels(unittest.TestCase):
    def setUp(self):
        self.app = create_app(app_config['testing'])
        self.app_ctx = self.app.app_context()
        self.app_ctx.push()
        app_database.create_all()

    def tearDown(self):
        app_database.session.remove()
        app_database.drop_all()
        self.app_ctx.pop()

    def test_question_answer_models(self):
        q1_content = 'question1 ?'
        q2_content = 'question2 ?'
        ans1_content = 'answer1.'
        ans2_content = 'answer2.'
        u1, u2 = User(username='testuser1'), User(username='testuser2')
        q1 = Question(question_content=q1_content, asker=u1, replier=u2)
        q2 = Question(question_content=q2_content, asker=u2, replier=u1)
        ans1 = Answer(answer_content=ans1_content, question=q1)
        ans2 = Answer(answer_content=ans2_content, question=q2)

        app_database.session.add_all([u1, u2, q1, q2])
        app_database.session.commit()

        self.assertEqual(u1.id, q1.asker_id)
        self.assertEqual(u2.id, q1.replier_id)

        app_database.session.add_all([ans1, ans2])
        app_database.session.commit()

        self.assertIs(q1.answer, ans1)
        self.assertIs(q2.answer, ans2)

        self.assertIs(ans1.question, q1)
        self.assertIs(ans2.question, q2)

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

    def test_user_roles_permissions(self):
        Role.populate_table()
        user_role = Role.query.filter(Role.role_name == 'user').first()
        admin_role = Role.query.filter(Role.role_name == 'admin').first()
        
        user = User(role=user_role)
        admin = User(role=admin_role)
        
        self.assertTrue(user.has_permissions(Role.roles['user']))
        self.assertFalse(user.is_admin())

        self.assertTrue(admin.has_permissions(Role.roles['admin']))
        self.assertTrue(admin.is_admin())

    def test_ask_qusetion_answer_question(self):
        q_content = 'question ?'
        ans_content = 'answer.'
        u1, u2 = User(username='testuser1'), User(username='testuser2')
        app_database.session.add_all([u1, u2])
        app_database.session.commit()

        u1.ask_question(question_content=q_content, question_recipient=u2)
        app_database.session.commit()

        question = Question.query.get(1)
        self.assertIsNotNone(question)

        u2.answer_question(answer_content=ans_content, question=question)
        app_database.session.commit()

        answer = Answer.query.get(1)
        self.assertIsNotNone(answer)

    def test_get_answered_unanswered_questions(self):
        q1_content = 'question1 ?'
        q2_content = 'question2 ?'
        q3_content = 'question3 ?'
        ans1_content = 'answer1.'
        ans2_content = 'answer2.'

        u1, u2 = User(username='testuser1'), User(username='testuser2')
        app_database.session.add_all([u1, u2])
        app_database.session.commit()

        u1.ask_question(question_content=q1_content, question_recipient=u2)
        u1.ask_question(question_content=q2_content, question_recipient=u2)
        u1.ask_question(question_content=q3_content, question_recipient=u2)
        app_database.session.commit()

        u2.answer_question(answer_content=ans1_content, question=u1.out_questions.first())
        u2.answer_question(answer_content=ans2_content, question=u1.out_questions.offset(1).first())
        app_database.session.commit()

        answered_questions = u2.get_answered_questions()
        self.assertEqual(len(answered_questions), 2)

        unanswered_questions = u2.get_unanswered_questions()
        self.assertEqual(len(unanswered_questions), 1)