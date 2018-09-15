from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Regexp, ValidationError
from app.models import User

validation_error_msgs = {
    'username_invalid' : 'username can be a combination of letters, dots, ' \
                         'numbers or underscores only',
    'username_used' : 'username already used',
    'email_used' : 'email is already registered',
    'email_invalid' : 'make sure you supplied your registered email address',
    'email_not_registered' : 'no user exists with this email address'
}


class SignInForm(FlaskForm):
    username = StringField('username', validators=[Required(), Length(1, 32)])
    password = PasswordField('password', validators=[Required()])
    remember_me = BooleanField('remember_me')
    recaptcha = RecaptchaField()
    submit = SubmitField('submit')

class SignUpForm(FlaskForm):
    username = StringField('username', validators=[Required(), Length(1, 32), 
                    Regexp('^[A-Za-z][A-Za-z0-9_.]*$', flags=0, message=validation_error_msgs['username_invalid'])])
    email = StringField('email', validators=[Required(), Length(1, 64)])
    password = PasswordField('password', validators=[Required()])
    recaptcha = RecaptchaField()
    submit = SubmitField('submit')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError(validation_error_msgs['username_used'])
        
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(validation_error_msgs['email_used'])

class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('current_password', validators=[Required()])
    new_password = PasswordField('new_password', validators=[Required()])
    recaptcha = RecaptchaField()
    submit = SubmitField('submit')

class EmailChangeForm(FlaskForm):
    current_email = StringField('current_email', validators=[Required(), Length(1, 64)])
    new_email = StringField('new_email', validators=[Required(), Length(1, 64)])
    recaptcha = RecaptchaField()
    submit = SubmitField('submit')

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def validate_new_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(validation_error_msgs['email_used'])

    def validate_current_email(self, field):
        if self.user.email != field.data:
            raise ValidationError(validation_error_msgs['email_invalid'])

class PasswordResetInitForm(FlaskForm):
    recaptcha = RecaptchaField()
    submit = SubmitField('Reset my password')


class PasswordResetRequestForm(FlaskForm):
    email = StringField('email', validators=[Required()])
    recaptcha = RecaptchaField()
    submit = SubmitField('submit')

    def validate_email(self, field):
        if not User.query.filter_by(email=field.data).first():
            raise ValidationError(validation_error_msgs['email_not_registered'])

class PasswordResetForm(FlaskForm):
    password = PasswordField('password', validators=[Required()])
    recaptcha = RecaptchaField()
    submit = SubmitField('submit')