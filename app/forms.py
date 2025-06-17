

from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, BooleanField, SubmitField,
                     SelectField, TextAreaField, IntegerField, TimeField)
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Optional
from wtforms_sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from app.models import User, Term, Course



class RegistrationForm(FlaskForm):
    username = StringField('نام کاربری', validators=[DataRequired()])
    email = StringField('ایمیل', validators=[DataRequired(), Email()])
    password = PasswordField('رمز عبور', validators=[DataRequired()])
    password2 = PasswordField(
        'تکرار رمز عبور', validators=[DataRequired(), EqualTo('password', message='رمزهای عبور باید یکسان باشند.')])
    role = SelectField('نقش', choices=[('student', 'دانشجو'), ('instructor', 'استاد')], validators=[DataRequired()])
    submit = SubmitField('ثبت‌نام')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('این نام کاربری قبلاً استفاده شده است.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('این ایمیل قبلاً ثبت شده است.')


class LoginForm(FlaskForm):
    username = StringField('نام کاربری', validators=[DataRequired()])
    password = PasswordField('رمز عبور', validators=[DataRequired()])
    remember_me = BooleanField('مرا به خاطر بسپار')
    submit = SubmitField('ورود')


class EditProfileForm(FlaskForm):
    username = StringField('نام کاربری', validators=[DataRequired()])
    email = StringField('ایمیل', validators=[DataRequired(), Email()])
    password = PasswordField('رمز عبور جدید', validators=[Optional()])
    password2 = PasswordField(
        'تکرار رمز عبور جدید',
        validators=[Optional(), EqualTo('password', message='رمزهای عبور باید یکسان باشند.')]
    )
    submit = SubmitField('ذخیره تغییرات')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('این نام کاربری قبلاً استفاده شده است.')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=self.email.data).first()
            if user is not None:
                raise ValidationError('این ایمیل قبلاً ثبت شده است.')




def instructor_query():

    return User.query.filter_by(role='instructor').order_by(User.username)

def term_query():

    return Term.query.order_by(Term.name.desc())

def course_query():

    return Course.query.order_by(Course.title)


class CourseForm(FlaskForm):
    title = StringField('عنوان دوره', validators=[DataRequired()])
    description = TextAreaField('توضیحات', validators=[DataRequired()])
    instructor = QuerySelectField('استاد', query_factory=instructor_query, get_label='username', allow_blank=False)
    term = QuerySelectField('ترم تحصیلی', query_factory=term_query, get_label='name', allow_blank=False)
    prereqs = QuerySelectMultipleField(
        'پیشنیازها (برای انتخاب چند مورد، کلید Ctrl را نگه دارید)',
        query_factory=course_query,
        get_label='title',
        allow_blank=True
    )
    day_of_week = SelectField('روز هفته', choices=[
        ('Saturday', 'شنبه'), ('Sunday', 'یکشنبه'), ('Monday', 'دوشنبه'),
        ('Tuesday', 'سه‌شنبه'), ('Wednesday', 'چهارشنبه'), ('Thursday', 'پنج‌شنبه'), ('Friday', 'جمعه')
    ], validators=[DataRequired()])
    start_time = TimeField('ساعت شروع', validators=[DataRequired()])
    end_time = TimeField('ساعت پایان', validators=[DataRequired()])
    capacity = IntegerField('ظرفیت', validators=[DataRequired()])
    submit = SubmitField('ذخیره دوره')


class TermForm(FlaskForm):
    name = StringField('نام ترم (مثال: پاییز ۱۴۰۴)', validators=[DataRequired()])
    is_active = BooleanField('آیا این ترم فعال برای ثبت‌نام است؟')
    submit = SubmitField('ذخیره ترم')