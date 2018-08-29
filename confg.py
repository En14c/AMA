import os


class AppConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class AppDevelopmentConfig(AppConfig):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URI')

class AppTestingConfig(AppConfig):
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URI')

class AppProductionConfig(AppConfig):
    SQLALCHEMY_DATABASE_URI = os.environ.get('PROD_DATABASE_URI')


app_config = {
    'testing' : AppTestingConfig,
    'development' : AppDevelopmentConfig,
    'production' : AppProductionConfig
}
