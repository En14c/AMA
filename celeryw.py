import os
from app import create_app, app_celery
from app.email import send_mail
from confg import app_config

app = create_app(app_config[os.environ.get('APPLICATION_STATE')])
app.app_context().push()