import os

class TokenExpirationTime:
    AFTER_0_MIN = 0
    AFTER_5_MIN = 300
    AFTER_10_MIN = 600
    AFTER_15_MIN = 900
    AFTER_1_HOUR = 3600

class AppConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = os.environ.get('MAIL_PORT')
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_SENDER = os.environ.get('MAIL_SENDER')
    ADMIN_MAIL_LIST = os.environ.get('ADMIN_MAIL_LIST').split(', ')
    RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_SITE_KEY')
    RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_SECRET_KEY')
    API_USERS_PER_PAGE = 20
    API_FOLLOWERS_PER_PAGE = API_USERS_PER_PAGE
    API_FOLLOWED_USERS_PER_PAGE = API_FOLLOWERS_PER_PAGE
    API_ANSWERED_QUESTIONS_PER_PAGE = 20
    API_UNANSWERED_QUESTIONS_PER_PAGE = API_ANSWERED_QUESTIONS_PER_PAGE

class AppDevelopmentConfig(AppConfig):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URI')

class AppTestingConfig(AppConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    MAIL_IMAP4_SERVER = os.environ.get('MAIL_IMAP4_SERVER')
    MAIL_TEST_SUBJECT = 'AMA-mail-testing'
    MAIL_TEST_TEMPLATE = 'email/mail_test.txt'
    ADMIN_MAIL_LIST = ['admin@mail.com']
    RECAPTCHA_PUBLIC_KEY = '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI'
    RECAPTCHA_PRIVATE_KEY = '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe'
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URI')

class AppProductionConfig(AppConfig):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

app_config = {
    'testing' : AppTestingConfig,
    'development' : AppDevelopmentConfig,
    'production' : AppProductionConfig
}
