import os

class AppConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_SENDER = os.environ.get('MAIL_SENDER')

class AppDevelopmentConfig(AppConfig):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URI')

class AppTestingConfig(AppConfig):
    WTF_CSRF_ENABLED = False
    MAIL_IMAP4_SERVER = 'imap.gmail.com'
    MAIL_TEST_SUBJECT = 'AMA-mail-testing'
    MAIL_TEST_TEMPLATE = 'email/mail_test.txt'
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URI')

class AppProductionConfig(AppConfig):
    SQLALCHEMY_DATABASE_URI = os.environ.get('PROD_DATABASE_URI')


app_config = {
    'testing' : AppTestingConfig,
    'development' : AppDevelopmentConfig,
    'production' : AppProductionConfig
}
