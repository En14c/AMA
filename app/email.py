import os
from flask import render_template
from flask_mail import Message
from app import app_mail
from app import app_celery


@app_celery.task(serializer='pickle')
def ama_send_mail(email_msg):
    app_mail.send(email_msg)


def send_mail(subject, to, template, **kwargs):
    ''' only plain text emails are used'''
    mail_msg = Message(subject=subject, recipients=[to], sender=os.environ.get('MAIL_SENDER'))
    mail_msg.body = render_template(template, **kwargs)
    ama_send_mail.delay(mail_msg)