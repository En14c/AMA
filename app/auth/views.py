import hashlib, os
from urllib.parse import urlparse
from itsdangerous import TimedJSONWebSignatureSerializer, BadSignature
from werkzeug.exceptions import NotFound
from flask import url_for, request, redirect, render_template, flash, current_app, session, abort
from flask_login import current_user, login_user, logout_user, login_required
from confg import TokenExpirationTime
from .. import app_login_manager, app_database
from ..models import User, Role
from .forms import SignInForm, SignUpForm, PasswordChangeForm, EmailChangeForm, \
                    PasswordResetForm, PasswordResetInitForm, PasswordResetRequestForm
from . import auth
from ..email import send_mail


@app_login_manager.user_loader
def load_user_object(user_id):
    return User.query.get(int(user_id))


@auth.before_app_request
def intercept_request():
    if current_user.is_authenticated and not current_user.account_confirmed \
            and not (request.path.startswith('/auth') or request.path.startswith('/static')):
        return redirect(url_for('auth.unconfirmed_account'))


@auth.route('/signin', methods=['GET', 'POST'])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    signin_form = SignInForm()
    if signin_form.validate_on_submit():
        user = User.query.filter_by(username=signin_form.username.data).first()
        if user is not None and user.check_password(signin_form.password.data):
            login_user(user, remember=signin_form.remember_me.data)
            flash('you have logged in successfully', category='info')
            if request.args.get('next'):
                next_param = urlparse(request.args.get('next'))
                if next_param.netloc:
                    return redirect(url_for('main.home'))
            return redirect(request.args.get('next') or url_for('main.home'))
        flash('invalid username or password', category='error')
    return render_template('auth/signin.html', form=signin_form)


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    signup_form = SignUpForm()
    if signup_form.validate_on_submit():
        if signup_form.email.data in current_app.config['ADMIN_MAIL_LIST']:
            role = Role.query.filter(Role.role_name == 'admin').first()
        else:
            role = Role.query.filter(Role.role_name == 'user').first()
        new_user = User(username=signup_form.username.data, email=signup_form.email.data,
                        password=signup_form.password.data, role=role)
        app_database.session.add(new_user)
        app_database.session.commit() #new_user object gets assigned an id after a database transaction
        confirmation_token = new_user.create_confirmation_token()
        send_mail.delay('Account Confirmation', to=new_user.email, 
                        template='email/confirmation_mail.txt',
                        confirmation_token=confirmation_token, username=new_user.username)
        flash('you are now registered .. you can login now', category='info')
        return redirect(url_for('auth.signin'))
    return render_template('auth/signup.html', form=signup_form)


@auth.route('/signout')
@login_required
def signout():
    logout_user()
    flash('you have been logged out successfully', category='info')
    return redirect(url_for('auth.signin'))


@auth.route('/accountconfirmation/c/c/<confirmation_token>')
@login_required
def confirm_account(confirmation_token):
    #user clicks the link more than once
    if current_user.account_confirmed:
        return redirect(url_for('main.home'))
    if current_user.verify_confirmation_token(confirmation_token):
        flash('you have confirmed your account', category='info')
    else:
        flash('your confirmation link has expired', category='errors')
    return redirect(url_for('main.home'))


@auth.route('/accountconfirmation/c/r')
@login_required
def resend_account_confirmation_email():
    confirmation_token = current_user.create_confirmation_token()
    send_mail.delay('Account Confirmation', to=current_user.email, 
                    template='email/confirmation_mail.txt',
                    confirmation_token=confirmation_token, username=current_user.username)
    flash('an account confirmation email has been sent to you', category='info')
    return redirect(url_for('main.home'))

@auth.route('/unconfirmedaccount')
@login_required
def unconfirmed_account():
    if current_user.account_confirmed:
        return redirect(url_for('main.home'))
    return render_template('auth/unconfirmed_account.html', user=current_user)

@auth.route('/passwordupdate', methods=['GET', 'POST'])
@login_required
def change_password():
    form = PasswordChangeForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.password = form.new_password.data
            flash('your password have been updated successfully', category='info')
            return redirect(url_for('main.home'))
        flash('your current password does not match the one you have entered', category='error')
    return render_template('auth/change_password.html', form=form)

@auth.route('/changeemail', methods=['GET', 'POST'])
@login_required
def change_email_address():
    form = EmailChangeForm()
    if form.validate_on_submit():
        serializer = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], 
                                                     expires_in=TokenExpirationTime.AFTER_5_MIN)
        token_payload = {'new_email': form.new_email.data}
        token = serializer.dumps(token_payload)
        send_mail.delay('Email Confirmation', to=form.new_email.data, 
                        template='email/email_change_confirmation.txt', 
                        confirmation_token=token, 
                        username=current_user.username)
        flash('check your inbox, you should have received a confirmation email', category='info')
        return redirect(url_for('main.home'))
    return render_template('auth/change_email.html', form=form)

@auth.route('/confirmnewemail/<confirmation_token>')
@login_required
def confirm_new_email_address(confirmation_token):
    serializer = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
    try:
        token_payload = serializer.loads(confirmation_token)
    except BadSignature:
        flash('confirmation link is invalid or has expired, your email address have not been updated', 
              category='error')
        return redirect(url_for('main.home'))
    current_user.email = token_payload['new_email']
    flash('your email address have been updated successfully', category='info')
    return redirect(url_for('main.home'))

@auth.route('/passwordreset', methods=['GET', 'POST'])
def password_reset_init():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = PasswordResetInitForm()
    if form.validate_on_submit():
        serializer = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], 
                                                     expires_in=TokenExpirationTime.AFTER_5_MIN)
        token_payload = {'password-reset': hashlib.md5(os.urandom(2)).hexdigest()}
        token = serializer.dumps(token_payload)
        return redirect(url_for('auth.password_reset_request', token=token))
    return render_template('auth/password_reset/password_reset_init.html', form=form)

@auth.route('/passwordreset/r/<token>', methods=['GET', 'POST'])
def password_reset_request(token):
    validate_request_source = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
    try:
        validate_request_source.loads(token)
    except BadSignature:
        abort(NotFound.code)
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        serializer = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], 
                                                     expires_in=TokenExpirationTime.AFTER_5_MIN)
        token_payload = {'email': form.email.data}
        token = serializer.dumps(token_payload)
        send_mail.delay('Password Reset Request', to=form.email.data, 
                        confirmation_token=token,
                        template='email/password_reset_email.txt')
        session['password-reset-request'] = hashlib.md5(os.urandom(2)).hexdigest()
        flash('a password reset link has been sent to your email address', category='info')
        return redirect(url_for('auth.signin'))
    return render_template('auth/password_reset/password_reset_request.html', form=form)

@auth.route('/passwordreset/r/u/<confirmation_token>', methods=['GET', 'POST'])
def password_reset_confirm(confirmation_token):
    #present 404 error to users who request the url directly not through password reset email
    if not session.get('password-reset-request'):
        abort(NotFound.code)
    serializer = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
    try:
        user_email = serializer.loads(confirmation_token).get('email')
    except BadSignature:
        flash('confirmation link is invalid or has expired', category='error')
        session.pop('password-reset-request')
        return redirect(url_for('auth.signin'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=user_email).first()
        if user:
            user.password = form.password.data
            flash('your password have been updated successfully', category='info')
        session.pop('password-reset-request')
        return redirect(url_for('auth.signin'))
    return render_template('auth/password_reset/password_reset.html', form=form)