from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp
from AYLB_LOGIS.models import User
from wtforms.validators import ValidationError

class RegistrationForm(FlaskForm):
    username = StringField('username', validators=[DataRequired(), Length(min=5, max=20)])
    first_name = StringField('firstname', validators=[DataRequired(), Length(min=1, max=20)])
    last_name = StringField('lastname', validators=[DataRequired(), Length(min=1, max=20)])
    email = StringField('email', validators=[DataRequired(), Email()])
    mobile_no = StringField('mobileno', validators=[DataRequired(), Length(min=10, max=10), Regexp(r'^\d+$', message='Mobile number must contain only digits')])
    password = PasswordField('password', validators=[DataRequired()])
    confirm_password = PasswordField('confirm_password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self,username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(f'Username:  {user.username} already exists, Please try with different one')
        
    def validate_email(self,email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(f'email:  {user.email} already exists, Please try with different one')

class LoginForm(FlaskForm):
    email = StringField('email', validators=[DataRequired(), Email()])
    password = PasswordField('password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')
