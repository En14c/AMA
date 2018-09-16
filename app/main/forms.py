from wtforms import StringField, SelectField, BooleanField, TextAreaField, SubmitField
from wtforms.validators import Required, Length, ValidationError
from flask_wtf import RecaptchaField, FlaskForm
from ..models import User, Role

validation_error_msgs = {
    'username_used' : 'username already used',
    'user_not_exist' : 'no user exist with this username',
    'email_used' : 'email is already registered'
}

class UserProfileEditForm(FlaskForm):
    username = StringField('username', validators=[Required(), Length(1, 32)])
    about_me = TextAreaField('about_me', validators=[Length(0, 300)])
    recaptcha = RecaptchaField()
    submit = SubmitField('submit')

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def validate_username(self, field):
        if self.user.username != field.data and \
                     User.query.filter(User.username == field.data).first():
            raise ValidationError(validation_error_msgs['username_used'])

class AccountsControlForm(FlaskForm):
    username = StringField('username', validators=[Required()])
    recaptcha = RecaptchaField()
    submit = SubmitField('submit')

    def validate_username(self, field):
        if not User.query.filter(User.username == field.data).first():
            raise ValidationError(validation_error_msgs['user_not_exist'])

class UserAccountControlForm(FlaskForm):
    """used by admin users to control other accounts"""
    email = StringField('email address', validators=[Required(), Length(1, 64)])
    account_confirmation = BooleanField('account_confirmation')
    user_role = SelectField('user_role', coerce=int)
    recaptcha = RecaptchaField()
    submit = SubmitField('submit')
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_role.choices = [(role.id, role.role_name) for role in Role.query.all()]
        self.user = user
    
    def validate_email(self, field):
        if self.user.email != field.data and \
                     User.query.filter(User.email == field.data).first():
            raise ValidationError(validation_error_msgs['email_used'])