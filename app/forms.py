
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from app.models import User

from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField,TextAreaField, IntegerField, TimeField
from wtforms_sqlalchemy.fields import QuerySelectField
from app.models import User

from wtforms.validators import Optional

# Registration Form
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    role = SelectField('Your Role', choices=[('student', 'Student'), ('instructor', 'Instructor')], validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('This username is already taken. Please choose another one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('This email address is already registered.')

# Login Form
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')


def instructor_query():
    return User.query.filter_by(role='instructor')

class CourseForm(FlaskForm):
    title = StringField('Course Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    # این فیلد به صورت یک منوی کشویی، لیست اساتید را نمایش می‌دهد
    instructor = QuerySelectField('Instructor',query_factory=instructor_query,get_label='username',allow_blank=False)
    day_of_week = SelectField('Day of Week', choices=[
        ('Saturday', 'Saturday'), ('Sunday', 'Sunday'), ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'), ('Thursday', 'Thursday'), ('Friday', 'Friday')
    ], validators=[DataRequired()])
    start_time = TimeField('Start Time', validators=[DataRequired()])
    end_time = TimeField('End Time', validators=[DataRequired()])
    capacity = IntegerField('Capacity', validators=[DataRequired()])
    submit = SubmitField('Save Course')

class EditProfileForm (FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('New Password', validators=[Optional()])
    password2 = PasswordField('Confirm New Password', validators=[Optional(),EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Save Changes')

    def __init__(self, original_username,original_email, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('This username is already taken.')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=self.email.data).first()
            if user is not None:
                raise ValidationError('This email address is already registered.')
