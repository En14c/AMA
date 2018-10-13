import os, unittest, random
from app import create_app, app_database
from app.models import User, Role, Question, Answer, AppPermissions, Follow
from confg import app_config


app = create_app(app_config[os.environ.get('APPLICATION_STATE')])

@app.cli.command()
def app_test():
    """ run application's unit tests """
    test_suite = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(test_suite)

@app.cli.command()
def generate_random_data():
    """ generates random data for the development enivronment """
    app_database.create_all()

    Role.populate_table()
    User.generate_fake_users()

    print('[+] generating random data...')
    print('[+] use the following user account to login and test the application\n')

    for i in range(1, User.query.count() + 1):
        user = User.query.get(i)
        User.generate_fake_followers(user.username)
        User.generate_fake_followed_users(user.username)
        User.generate_fake_questions(user.username)
        User.generate_fake_answers(user.username)

    user = User.query.get(random.randint(1, User.query.count())); user.password = '123'
    print('username:{username}\nemail:{email}\npassword: {password}\n\n'.format(username=user.username,
                                                                                email=user.email,
                                                                                password='123'))
    print('[+] done')

@app.shell_context_processor
def create_shell_context():
    return dict(app=app, db=app_database, User=User, Role=Role, Question=Question, Answer=Answer,
                AppPermissions=AppPermissions, Follow=Follow)