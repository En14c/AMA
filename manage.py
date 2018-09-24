import os, unittest
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
    print('[+] use the following user accounts to login and test the application\n')

    for i in range(0, 3):
        user = User.query.get(i + 1)
        User.generate_fake_followers(user.username)
        User.generate_fake_followed_users(user.username)
        User.generate_fake_questions(user.username)
        User.generate_fake_answers(user.username)

        
        #make sure that at least 3 followed users have fake Q&A to fill the the user's home page
        followed_users = user.get_followed_users_list()[0:3]
        for followed_user in followed_users:
            User.generate_fake_followers(followed_user.username)
            User.generate_fake_followed_users(followed_user.username)
            User.generate_fake_questions(followed_user.username)
            User.generate_fake_answers(followed_user.username)

        user.password = '123'
        print('username:{username}\nemail:{email}\npassword: {password}\n\n'.format(username=user.username,
                                                                                    email=user.email,
                                                                                    password='123'))
    print('[+] done')

@app.shell_context_processor
def create_shell_context():
    return dict(app=app, db=app_database, User=User, Role=Role, Question=Question, Answer=Answer,
                AppPermissions=AppPermissions, Follow=Follow)