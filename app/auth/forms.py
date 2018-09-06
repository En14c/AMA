from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length, Regexp, ValidationError
from app.models import User

validation_error_msgs = {
    'username_invalid' : 'username can be a combination of letters, dots, ' \
                         'numbers or underscores only',
    'username_used' : 'username already used',
    'email_used' : 'email is already registered'
}


class SignInForm(FlaskForm):
    username = StringField('username', validators=[Required(), Length(1, 32)])
    password = PasswordField('password', validators=[Required()])
    remember_me = BooleanField('remember_me')
    submit = SubmitField('submit')

class SignUpForm(FlaskForm):
    username = StringField('username', validators=[Required(), Length(1, 32), 
                    Regexp('^[A-Za-z][A-Za-z0-9_.]*$', flags=0, message=validation_error_msgs['username_invalid'])])
    email = StringField('email', validators=[Required(), Length(1, 64)])
    password = PasswordField('password', validators=[Required()])
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
    submit = SubmitField('submit')

class EmailChangeForm(FlaskForm):
    current_email = StringField('current_email', validators=[Required(), Length(1, 64)])
    new_email = StringField('new_email', validators=[Required(), Length(1, 64)])
    submit = SubmitField('submit')

    def validate_new_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(validation_error_msgs['email_used'])