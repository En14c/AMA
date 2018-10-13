a web-application similar to [ ask.fm ] to get my hands dirty with flask-framework

learning-resources:
- Flask Web Development: Developing Web Applications with Python [book]
- [SQLAlchemy ORM / WTForms /jinja2 / celery / the used flask extensions ]'s documentation
- other resources

celery is used as the task queue (so far it's used only in the application to send asynchronous emails) and rabbitmq as the message broker

running the application locally:
check the app_run.txt file