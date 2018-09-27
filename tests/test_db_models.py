import unittest, time
from faker import Faker
from app import create_app, app_database
from app.models import User, Role, Question, Answer, Follow
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

class TestFollowModel(unittest.TestCase):
    def setUp(self):
        self.app = create_app(app_config['testing'])
        self.app_ctx = self.app.app_context()
        self.app_ctx.push()
        app_database.create_all()

    def tearDown(self):
        app_database.session.remove()
        app_database.drop_all()
        self.app_ctx.pop()

    def test_follow_model(self):
        fake = Faker()
        user1 = User(username=fake.user_name())
        user2 = User(username=fake.user_name())

        app_database.session.add_all([user1, user2])
        app_database.session.commit()

        follow1 = Follow(follower=user1, followed=user2)
        app_database.session.add(follow1)
        app_database.session.commit()

        self.assertEqual(user1.follows.count(), 1)
        self.assertEqual(user2.followed_by.count(), 1)

        self.assertEqual(user1.follows.first().followed.username, user2.username)
        self.assertEqual(user2.followed_by.first().follower.username, user1.username)

        app_database.session.delete(user1)
        app_database.session.commit()

        self.assertIsNone(Follow.query.get(1))

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

    def test_is_question_replier_asker(self):
        fake = Faker()
        q_content = fake.sentence(nb_words=6, variable_nb_words=True, ext_word_list=None)
        ans_content = fake.sentence(nb_words=6, variable_nb_words=True, ext_word_list=None)
        testuser1 = User(username=fake.user_name())
        testuser2 = User(username=fake.user_name())
        app_database.session.add_all([testuser1, testuser2])
        app_database.session.commit()

        testuser1.ask_question(question_content=q_content, question_recipient=testuser2)
        app_database.session.commit()

        question = Question.load_question_by_id(1)
        self.assertIsNotNone(question)

        self.assertFalse(testuser1.is_question_replier(question))
        self.assertTrue(testuser2.is_question_replier(question))

        self.assertTrue(testuser1.is_question_asker(question))
        self.assertFalse(testuser2.is_question_asker(question))

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
        q_content = 'question{}?'
        ans_content = 'answer{}'

        u1, u2 = User(username='testuser1'), User(username='testuser2')
        app_database.session.add_all([u1, u2])
        app_database.session.commit()

        u1.ask_question(question_content=q_content.format(1), question_recipient=u2)
        u1.ask_question(question_content=q_content.format(2), question_recipient=u2)
        u1.ask_question(question_content=q_content.format(3), question_recipient=u2)
        u1.ask_question(question_content=q_content.format(4), question_recipient=u2)
        app_database.session.commit()

        u2.answer_question(answer_content=ans_content.format(1), question=u1.out_questions.first())
        u2.answer_question(answer_content=ans_content.format(2), question=u1.out_questions.offset(1).first())
        app_database.session.commit()

        self.assertTrue(u2.in_questions.first().has_answer)
        self.assertTrue(u2.in_questions.offset(1).first().has_answer)
        self.assertFalse(u2.in_questions.offset(2).first().has_answer)
        self.assertFalse(u2.in_questions.offset(3).first().has_answer)

        answered_questions = u2.get_answered_questions()
        self.assertEqual(len(answered_questions), 2)
        answered_questions = u2.get_answered_questions(1)
        self.assertEqual(len(answered_questions), 1)

        unanswered_questions = u2.get_unanswered_questions()
        self.assertEqual(len(unanswered_questions), 2)
        unanswered_questions = u2.get_unanswered_questions(1)
        self.assertEqual(len(unanswered_questions), 1)

    def test_get_followers_followed_list(self):
        fake = Faker()
        user1 = User(username=fake.user_name())
        user2 = User(username=fake.user_name())

        app_database.session.add_all([user1, user2])
        app_database.session.commit()

        follow1 = Follow(follower=user1, followed=user2)
        app_database.session.add(follow1)
        app_database.session.commit()

        followers_list = user2.get_followers_list()
        self.assertEqual(len(followers_list), 1)
        self.assertEqual(followers_list[0].username, user1.username)

        followed_list = user1.get_followed_users_list()
        self.assertEqual(len(followed_list), 1)
        self.assertEqual(followed_list[0].username, user2.username)

    def test_is_following_followed_by(self):
        fake = Faker()
        user1 = User(username=fake.user_name())
        user2 = User(username=fake.user_name())

        app_database.session.add_all([user1, user2])
        app_database.session.commit()

        follow1 = Follow(follower=user1, followed=user2)
        app_database.session.add(follow1)
        app_database.session.commit()

        self.assertTrue(user2.is_followed_by(user1))
        self.assertTrue(user1.is_following(user2))

        self.assertFalse(user2.is_followed_by(user2))
        self.assertFalse(user1.is_following(user1))

    def test_follow_unfollow(self):
        fake = Faker()
        user1 = User(username=fake.user_name())
        user2 = User(username=fake.user_name())

        app_database.session.add_all([user1, user2])
        app_database.session.commit()

        user1.follow(user2)
        user1.follow(user1)
        app_database.session.commit()

        #user can not follow himself
        self.assertEqual(user1.follows.count(), 1)

        self.assertIsNotNone(user1.follows.first())
        self.assertIsNotNone(user2.followed_by.first())

        self.assertEqual(user1.follows.first().followed.username, user2.username)
        self.assertEqual(user2.followed_by.first().follower.username, user1.username)


        user1.unfollow(user2)
        app_database.session.commit()

        self.assertIsNone(user1.follows.first())
        self.assertIsNone(user2.followed_by.first())