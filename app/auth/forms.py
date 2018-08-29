from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length


class SignInForm(FlaskForm):
    username = StringField('username', validators=[Required(), Length(1, 32)])
    password = PasswordField('password', validators=[Required()])
    remember_me = BooleanField('remember_me')
    submit = SubmitField('submit')