from flask import render_template
from werkzeug.exceptions import NotFound, InternalServerError
from . import main

@main.app_errorhandler(NotFound)
def page_not_found(ex):
    return render_template('main/errors/404.html'), NotFound.code

@main.app_errorhandler(InternalServerError)
def internal_server_error(ex):
    return render_template('main/errors/500.html'), InternalServerError.code