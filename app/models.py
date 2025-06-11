from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import time


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False, default='student') # نقش‌ها: student, instructor, admin
    enrollments = db.relationship('Enrollment', backref='student', lazy='dynamic', foreign_keys='Enrollment.user_id')
    taught_courses = db.relationship('Course', backref='instructor', lazy='dynamic', foreign_keys='Course.instructor_id')
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    def __repr__(self):
        return f'<User {self.username}>'

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text)
    day_of_week = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    capacity = db.Column(db.Integer, default=20)
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    enrollments = db.relationship('Enrollment', backref='course', lazy='dynamic', foreign_keys='Enrollment.course_id')
    def __repr__(self):
        return f'<Course {self.title}>'

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    def __repr__(self):
        return f'<Enrollment user_id={self.user_id} course_id={self.course_id}>'

@login.user_loader
def load_user(id):
    return User.query.get(int(id))