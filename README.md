a web-application similar to [ ask.fm ] to get my hands dirty with flask-framework

learning-resources:
- Flask Web Development: Developing Web Applications with Python [book]
- [SQLAlchemy ORM / WTForms /jinja2 / celery / the used flask extensions ]'s documentation
- other resources

celery is used as the task queue (so far it's used only in the application to send asynchronous emails) and rabbitmq as the message broker

how to run the application in development/production/testing state:
- look for the configuration options (in confg.py) that are loaded from the environment-variables and (provide them directly from the environment or with .env file). regarding the emails of the admins it's provided like this **ADMIN_MAIL_LIST=test@mail.com, test2@mail,com...**, the APPLICATION_STATE env var can be set to one of 3 values [testing, development, production]
- regarding the reCAPTCHA you can just use the site/public keys used for unit-testing or just register a key pair from ur reCAPTCHA panel
- replicate the python environment with pip install -r requirements.txt
- run **flask db upgrade** -> **flask db stamp a8176fce55e5** -> **flask db upgrade**
- run **flask generate_random_data** to generate random users/followers/answers/questions for the dev env
- run the celery worker **celery -A celeryw.app_celery worker --loglevel=info**
- run the application **flask run**
- if in **testing** state run **flask app_test** with the celery worker running in the background