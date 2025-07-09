from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import time

prerequisites = db.Table('prerequisites',
                         db.Column('course_id', db.Integer, db.ForeignKey('course.id'), primary_key=True),
                         db.Column('prerequisite_id', db.Integer, db.ForeignKey('course.id'), primary_key=True)
                         )


class Term(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False, unique=True)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    courses = db.relationship('Course', backref='term', lazy='dynamic')

    def __repr__(self):
        return f'<Term {self.name}>'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False, default='student')
    enrollments = db.relationship('Enrollment', backref='student', lazy='dynamic', foreign_keys='Enrollment.user_id')
    taught_courses = db.relationship('Course', backref='instructor', lazy='dynamic',
                                     foreign_keys='Course.instructor_id')

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
    credits = db.Column(db.Integer, nullable=False, default=3)
    day_of_week = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    capacity = db.Column(db.Integer, default=20)
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    term_id = db.Column(db.Integer, db.ForeignKey('term.id'), nullable=False)
    enrollments = db.relationship('Enrollment', backref='course', lazy='dynamic', foreign_keys='Enrollment.course_id')

    prereqs = db.relationship(
        'Course', secondary=prerequisites,
        primaryjoin=(prerequisites.c.course_id == id),
        secondaryjoin=(prerequisites.c.prerequisite_id == id),
        backref=db.backref('is_prereq_for', lazy='dynamic'),
        lazy='dynamic'
    )

    def __repr__(self):
        return f'<Course {self.title}>'


class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    status = db.Column(db.String(20), default='enrolled', nullable=False)
    grade = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f'<Enrollment user_id={self.user_id} course_id={self.course_id}>'


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
