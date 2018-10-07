from flask import jsonify
from werkzeug.exceptions import Forbidden

def api_forbidden():
    return jsonify({
        'status_code': Forbidden.code,
        'error_msg': Forbidden.description
    })