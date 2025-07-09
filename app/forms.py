from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, BooleanField,
                     SubmitField, SelectField, TextAreaField,
                     IntegerField, TimeField)
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Optional, InputRequired, NumberRange
from wtforms_sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from app.models import User, Term, Course

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
    credits = IntegerField('تعداد واحد', validators=[DataRequired(), NumberRange(min=1, max=4)])
    day_of_week = SelectField('روز هفته', choices=[
        ('Saturday', 'شنبه'), ('Sunday', 'یکشنبه'), ('Monday', 'دوشنبه'),
        ('Tuesday', 'سه‌شنبه'), ('Wednesday', 'چهارشنبه'), ('Thursday', 'پنج‌شنبه')
    ], validators=[DataRequired()])
    start_time = TimeField('ساعت شروع', validators=[DataRequired()])
    end_time = TimeField('ساعت پایان', validators=[DataRequired()])
    capacity = IntegerField('ظرفیت', validators=[DataRequired()])
    submit = SubmitField('ذخیره دوره')

class TermForm(FlaskForm):
    name = StringField('نام ترم (مثال: پاییز ۱۴۰۴)', validators=[DataRequired()])
    is_active = BooleanField('آیا این ترم فعال برای ثبت‌نام است؟')
    submit = SubmitField('ذخیره ترم')

class AdminCreateUserForm(FlaskForm):
    username = StringField('نام کاربری', validators=[DataRequired()])
    email = StringField('ایمیل', validators=[DataRequired(), Email()])
    password = PasswordField('رمز عبور موقت', validators=[DataRequired()])
    role = SelectField('نقش', choices=[('student', 'دانشجو'), ('instructor', 'استاد')], validators=[DataRequired()])
    submit_create = SubmitField('ایجاد کاربر')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('این نام کاربری قبلاً استفاده شده است.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('این ایمیل قبلاً ثبت شده است.')

class ChangeRoleForm(FlaskForm):
    role = SelectField('نقش جدید', choices=[('student', 'دانشجو'), ('instructor', 'استاد')])
    submit_change = SubmitField('ذخیره')

class GradeForm(FlaskForm):
    grade = IntegerField('نمره',
        validators=[
            InputRequired(),
            NumberRange(min=0, max=20, message='نمره باید بین ۰ و ۲۰ باشد')
        ]
    )
    submit = SubmitField('ثبت')