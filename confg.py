import os

class AppConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SERVER_NAME = os.environ.get('SERVER_NAME')
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_SENDER = os.environ.get('MAIL_SENDER')
    RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_SITE_KEY')
    RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_SECRET_KEY')

class AppDevelopmentConfig(AppConfig):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URI')

class AppTestingConfig(AppConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    MAIL_IMAP4_SERVER = 'imap.gmail.com'
    MAIL_TEST_SUBJECT = 'AMA-mail-testing'
    MAIL_TEST_TEMPLATE = 'email/mail_test.txt'
    RECAPTCHA_PUBLIC_KEY = '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI'
    RECAPTCHA_PRIVATE_KEY = '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe'
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URI')

class AppProductionConfig(AppConfig):
    SQLALCHEMY_DATABASE_URI = os.environ.get('PROD_DATABASE_URI')


app_config = {
    'testing' : AppTestingConfig,
    'development' : AppDevelopmentConfig,
    'production' : AppProductionConfig
}
