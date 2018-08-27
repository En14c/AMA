import os
import unittest
from app import create_app, app_database
from app.models import User
from confg import app_config


app = create_app(app_config[os.environ.get('APPLICATION_STATE')])

@app.cli.command()
def app_test():
    """ run application's unit tests """
    test_suite = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(test_suite)


@app.shell_context_processor
def create_shell_context():
    return dict(app=app, db=app_database, User=User)


