from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp

class RegistrationForm(FlaskForm):
    username = StringField('username', validators=[DataRequired(), Length(min=5, max=20)])
    first_name = StringField('firstname', validators=[DataRequired(), Length(min=1, max=20)])
    last_name = StringField('lastname', validators=[DataRequired(), Length(min=1, max=20)])
    email = StringField('email', validators=[DataRequired(), Email()])
    mobile_no = StringField('mobileno', validators=[DataRequired(), Length(min=10, max=10), Regexp(r'^\d+$', message='Mobile number must contain only digits')])
    password = PasswordField('password', validators=[DataRequired()])
    confirm_password = PasswordField('confirm_password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('email', validators=[DataRequired(), Email()])
    password = PasswordField('password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')
