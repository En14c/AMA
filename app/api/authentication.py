from flask import g, request
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth, MultiAuth
from app.models import User, TokenExpirationTime
from .errors import api_forbidden
from . import api

api_basic_auth = HTTPBasicAuth()
api_token_auth = HTTPTokenAuth(scheme='Bearer')
api_multi_auth = MultiAuth(api_basic_auth, api_token_auth)

@api_basic_auth.verify_password
def api_verify_username_password(username, password):
    user = User.load_user_by_username(username)
    if not user or not user.check_password(password):
        return False
    g.current_api_user = user
    return True
    
@api_token_auth.verify_token
def api_verify_token(auth_token):
    user = User.api_load_user_from_auth_token(auth_token)
    if not user:
        return False
    g.current_api_user = user
    return True

@api.route('/gen-auth-token')
@api_multi_auth.login_required
def api_generate_auth_token():
    #user can get authentication token only if he don't have one already or have one but expired
    if g.current_api_user.api_auth_token and \
                        g.current_api_user.api_verify_auth_token(g.current_api_user.api_auth_token):
        return api_forbidden()
    token_expiration_time = request.args.get('expires_in', TokenExpirationTime.AFTER_15_MIN, int)
    g.current_api_user.api_generate_auth_token(expires_in=token_expiration_time)
    return g.current_api_user.api_get_auth_token_json()
