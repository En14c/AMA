from functools import wraps
from werkzeug.exceptions import Forbidden
from flask import abort
from flask_login import current_user

def permissions_required(permissions):
    def func_decorator(decorated_func):
        @wraps(decorated_func)
        def func_wrapper(*args, **kwargs):
            if not current_user.has_permissions(permissions):
                return abort(Forbidden.code)
            return decorated_func(*args, **kwargs)
        return func_wrapper
    return func_decorator
