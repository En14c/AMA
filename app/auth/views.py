from urllib.parse import urlparse
from flask import url_for, request, redirect, render_template
from flask_login import current_user, login_user, logout_user, login_required
from .. import app_login_manager
from ..models import User
from .forms import SignInForm
from . import auth


@app_login_manager.user_loader
def load_user_object(id):
    return User.query.get(int(id))


@auth.route('/signin', methods=['GET', 'POST'])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    signin_form = SignInForm()
    if signin_form.validate_on_submit():
        user = User.query.filter_by(username=signin_form.username.data).first()
        if user is not None and user.check_password(signin_form.password.data):
            login_user(user, remember=signin_form.remember_me.data)
            if request.args.get('next'):
                next_param = urlparse(request.args.get('next'))
                if next_param.netloc:
                    return redirect(url_for('main.home'))
            return redirect(request.args.get('next') or url_for('main.home'))
    return render_template('auth/signin.html', form=signin_form)
   

@auth.route('/signout')
@login_required
def signout():
    logout_user()
    return redirect(url_for('auth.signin'))