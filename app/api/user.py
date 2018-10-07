from flask import g, jsonify, current_app, request, abort
from werkzeug.exceptions import NotFound
from app.models import User
from .authentication import api_multi_auth
from . import api
from .errors import api_forbidden

@api.route('/users/')
@api_multi_auth.login_required
def api_get_users_list():
    users_per_page = request.args.get('n', current_app.config['API_USERS_PER_PAGE'], int)
    page_num = request.args.get('p', 1, int)
    return User.api_get_users_list_json(page=page_num, users_per_page=users_per_page)

@api.route('/users/<username>/')
@api_multi_auth.login_required
def api_get_user_profile_info(username):
    user = User.load_user_by_username(username)
    if not user:
        abort(NotFound.code)
    return jsonify(user.api_get_user_info())

@api.route('/users/<username>/followers')
@api_multi_auth.login_required
def api_get_followers_list(username):
    user = User.load_user_by_username(username)
    if not user:
        abort(NotFound.code)
    followers_per_page = request.args.get('n', current_app.config['API_FOLLOWERS_PER_PAGE'], int)
    page_num = request.args.get('p', 1, int)
    return User.api_get_followers_list_json(user=user, page=page_num, followers_per_page=followers_per_page)

@api.route('/users/<username>/following')
@api_multi_auth.login_required
def api_get_followed_users_list(username):
    user = User.load_user_by_username(username)
    if not user:
        abort(NotFound.code)
    followed_users_per_page = request.args.get('n', current_app.config['API_FOLLOWED_USERS_PER_PAGE'], int)
    page_num = request.args.get('p', 1, int)
    return User.api_get_followed_users_list_json(user=user, page=page_num, 
                                                 followed_users_per_page=followed_users_per_page)

@api.route('/users/<username>/answered-questions')
@api_multi_auth.login_required
def api_get_user_answered_questions(username):
    user = User.load_user_by_username(username)
    if not user:
        abort(NotFound.code)
    questions_per_page = request.args.get('n', current_app.config['API_ANSWERED_QUESTIONS_PER_PAGE'], int)
    page_num = request.args.get('p', 1, int)
    return User.api_get_answered_questions_json(user=user, page=page_num, 
                                                questions_per_page=questions_per_page)

@api.route('/users/<username>/unanswered-questions')
@api_multi_auth.login_required
def api_get_user_unanswered_questions(username):
    user = User.load_user_by_username(username)
    if not user:
        abort(NotFound.code)
    if g.current_api_user.id != user.id:
        return api_forbidden()
    questions_per_page = request.args.get('n', current_app.config['API_UNANSWERED_QUESTIONS_PER_PAGE'], int)
    page_num = request.args.get('p', 1, int)
    return User.api_get_unanswered_questions_json(user=user, page=page_num, 
                                                  questions_per_page=questions_per_page)