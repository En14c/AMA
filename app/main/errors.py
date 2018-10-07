from flask import render_template, request, jsonify
from werkzeug.exceptions import NotFound, InternalServerError
from . import main

@main.app_errorhandler(NotFound)
def page_not_found(ex):
    if request.accept_mimetypes.accept_json \
            and not request.accept_mimetypes.accept_html:
        return jsonify({
            'error_msg': NotFound.description,
            'status_code': NotFound.code
        })
    return render_template('main/errors/404.html'), NotFound.code

@main.app_errorhandler(InternalServerError)
def internal_server_error(ex):
    if request.accept_mimetypes.accept_json \
            and not request.accept_mimetypes.accept_html:
        return jsonify({
            'error_msg': InternalServerError.description,
            'status_code': InternalServerError.code
        })
    return render_template('main/errors/500.html'), InternalServerError.code