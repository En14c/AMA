import os
from flask import render_template, current_app
from flask_mail import Message, Mail
from app import app_celery

'''
according to the flask-mail extension's docs, when an Mail instance is created and configured
in this form => [ Mail_instance.init_app(app) ], then emails will be sent with the configuration 
values from flask's [ current_app ] context global
'''


@app_celery.task(serializer='pickle')
def send_mail(subject, to, template, **kwargs):
    '''only plain text emails are used'''

    #don't suppress email when unit-testing the app's email-sending functionality
    if kwargs.get('email_testing'):
        try:
            if current_app.config['TESTING']:
                current_app.config['TESTING'] = False
        except KeyError:
            pass

    __app__ = current_app._get_current_object()
    
    with __app__.test_request_context():
        app_mail = Mail()
        app_mail.init_app(current_app._get_current_object())
        mail_msg = Message(subject=subject, recipients=[to], sender=os.environ.get('MAIL_SENDER'))
        mail_msg.body = render_template(template, **kwargs)
        app_mail.send(mail_msg)