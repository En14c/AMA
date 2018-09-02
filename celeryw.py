import os
from app import create_app
from confg import app_config

from app import app_celery
from app.email import ama_send_mail


app = create_app(app_config[os.environ.get('APPLICATION_STATE')])
app.app_context().push()


