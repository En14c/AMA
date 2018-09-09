from urllib.parse import urlparse
from itsdangerous import TimedJSONWebSignatureSerializer, BadSignature, SignatureExpired
from flask import url_for, request, redirect, render_template, flash, current_app
from flask_login import current_user, login_user, logout_user, login_required
from .. import app_login_manager, app_database
from ..models import User
from .forms import SignInForm, SignUpForm, PasswordChangeForm, EmailChangeForm

from . import auth
from ..email import send_mail


@app_login_manager.user_loader
def load_user_object(id):
    return User.query.get(int(id))


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
        new_user = User(username=signup_form.username.data, email=signup_form.email.data,
                        password=signup_form.password.data)
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
        serializer = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], expires_in=300)
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
    except (BadSignature, SignatureExpired):
        flash('confirmation link is invalid or has expired, your email address have not been updated', 
              category='error')
        return redirect(url_for('main.home'))
    current_user.email = token_payload['new_email']
    flash('your email address have been updated successfully', category='info')
    return redirect(url_for('main.home'))