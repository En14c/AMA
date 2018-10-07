from functools import wraps
from flask import g
from .errors import api_forbidden

def api_permission_required(permissions):
    def func_decorator(decorated_func):
        @wraps(decorated_func)
        def func_wrapper(*args, **kwargs):
            if not g.current_user.has_permissions(permissions):
                return api_forbidden()
            return decorated_func(*args, **kwargs)
        return func_wrapper
    return func_decorator