from werkzeug.exceptions import NotFound
from itsdangerous import TimedJSONWebSignatureSerializer, BadSignature
from flask import render_template, abort, redirect, url_for, current_app
from flask_login import login_required, current_user
from confg import TokenExpirationTime
from app import app_database
from app.models import User, AppPermissions, Role
from ..decorators import permissions_required
from .forms import UserProfileEditForm, UserAccountControlForm, AccountsControlForm
from . import main

@main.app_context_processor
def templates_add_app_permissions():
    return dict(app_permissions=AppPermissions)

@main.route('/')
@login_required
def home():
    return render_template('main/home.html')

@main.route('/u/<username>')
@login_required
def user_profile(username):
    user = User.query.filter(User.username == username).first()
    if not user:
        abort(NotFound.code)
    return render_template('main/user/user_profile.html', user=user)

@main.route('/u/<username>/edit-profile', methods=['GET', 'POST'])
@login_required
def user_profile_edit(username):
    if current_user.username != username:
        abort(NotFound.code)
    form = UserProfileEditForm(current_user)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        app_database.session.add(current_user)
        return redirect(url_for('main.user_profile', username=current_user.username))
    form.username.data = current_user.username
    form.about_me.data = current_user.about_me
    return render_template('main/user/user_profile_edit.html', form=form)

@main.route('/accounts-control', methods=['GET', 'POST'])
@login_required
@permissions_required(AppPermissions.ADMINISTER)
def accounts_control():
    form = AccountsControlForm()
    if form.validate_on_submit():
        token_gen = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], 
                                                    expires_in=TokenExpirationTime.AFTER_5_MIN)
        token_payload = {'username': form.username.data}
        token = token_gen.dumps(token_payload)
        return redirect(url_for('main.user_account_control', 
                                username=form.username.data, token=token))
    return render_template('main/user/accounts_control.html', form=form)

@main.route('/u/account-control/<token>/<username>', methods=['GET', 'POST'])
@login_required
@permissions_required(AppPermissions.ADMINISTER)
def user_account_control(token, username):
    token_verify = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
    try:
        token_verify.loads(token)
    except BadSignature:
        abort(NotFound.code)
    user = User.query.filter(User.username == username).first()
    if not user:
        abort(NotFound.code)
    form = UserAccountControlForm(user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.account_confirmed = form.account_confirmation.data
        user.role = Role.query.get(form.user_role.data)
        app_database.session.add(user)
        return redirect(url_for('main.user_profile', username=current_user.username))
    form.email.data = user.email
    form.account_confirmation.data = user.account_confirmed
    form.user_role.data = user.role_id
    return render_template('main/user/user_account_control_admin.html', form=form)