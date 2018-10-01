from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, TextField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, Optional, URL
from app.models import User
from flask_babel import _, lazy_gettext as _l

class LoginForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Sign In'))


class RegistrationForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(_l('Repeat Password'), validators=[DataRequired(), EqualTo('password')])
    type = SelectField('Type of Account', choices=[('committee', 'Committee'), ('student', 'Student')], validators=[DataRequired()])
    submit = SubmitField(_l('Register'))

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(_l('Username already taken!'))

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(_l('Email Address is already registered!'))


class EditProfileForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    name = StringField(_l('Name'), validators=[DataRequired()])
    about_me = TextAreaField(_l('About The Committee'), validators=[Length(min=0, max=1000)])
    departments = StringField(_l('Departments'), validators=[DataRequired()])
    submit = SubmitField(_l('Save'))

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username = self.username.data).first()
            if user is not None:
                raise ValidationError(_l('Username Already Taken'))

class ManageForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    name = StringField(_l('Name'), validators=[DataRequired()])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    phone_number = StringField(_l('Phone'), validators=[DataRequired(),Length(min=10,max=10)])
    departments = StringField(_l('Departments Interested In'), validators=[DataRequired()])
    about_me = TextAreaField(_l('About Me (Max: 1000 Characters)'), validators=[Length(min=0, max=1000)])
    experience = TextAreaField(_l('My Experience (Max: 1000 Characters)'), validators=[Length(min=0, max=1000)])
    why = TextAreaField(_l('Why Me (Max: 1000 Characters)'), validators=[DataRequired(),Length(min=0, max=1000)])
    submit = SubmitField(_l('Save'))

    def __init__(self, original_username, *args, **kwargs):
        super(ManageForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username = self.username.data).first()
            if user is not None:
                raise ValidationError(_l('Username Already Taken'))

class PostEventForm(FlaskForm):
    event = StringField(_l('Event Name (Max: 50 Characters)'), validators=[DataRequired(), Length(min=1, max=50)])
    post = TextAreaField(_l('Description (Max: 250 Characters)'), validators=[
           DataRequired(), Length(min=1, max=250)])
    link = StringField(_l('Registration Link (Enter a https/http URL)'), validators=[Optional(strip_whitespace=True), URL()])
    type = SelectField('Type of Event', choices=[('event', 'Event'), ('recruitments', 'Recruitments')], validators=[DataRequired()])
    submit = SubmitField(_l('Add!'))

class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Request Password Reset'))

class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(_l('Repeat Password'), validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Save new Password'))
