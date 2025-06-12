from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required

from app import app, db
from app.forms import LoginForm, RegistrationForm
from app.models import User

from app.forms import CourseForm
from app.models import Course
from flask import abort

from app.models import Enrollment


@app.route('/')
@app.route('/index')
def index():
    if not current_user.is_authenticated:
        return render_template('home.html', title='Welcome')

    return render_template('index.html', title='Dashboard')


@app.route('/home')
def home():
    return render_template('home.html', title='Welcome')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        flash('You have logged in successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/course/new', methods=['GET', 'POST'])
@login_required
def create_course():
    if current_user.role not in ['admin', 'instructor']:
        abort(403)

    form = CourseForm()
    if current_user.role == 'instructor' and request.method == 'POST':
        form.instructor.data = current_user
    if form.validate_on_submit():
        new_course = Course(
            title=form.title.data,
            description=form.description.data,
            instructor_id=form.instructor.data.id,
            day_of_week=form.day_of_week.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            capacity=form.capacity.data
        )
        db.session.add(new_course)
        db.session.commit()
        flash('New course has been created successfully!', 'success')
        return redirect(url_for('manage_courses'))
    return render_template('course_form.html', title='Create Course', form=form, legend='Create a New Course')


@app.route('/manage/courses')
@login_required
def manage_courses():
    if current_user.role not in ['admin', 'instructor']:
        abort(403)

    if current_user.role == 'admin':
        courses = Course.query.all()
    else:
        courses = Course.query.filter_by(instructor_id=current_user.id).all()
    return render_template('manage_courses.html', title='Manage Courses', courses=courses)


@app.route('/course/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)

    if current_user.role != 'admin' and course.instructor_id != current_user.id:
        abort(403)

    form = CourseForm()

    if form.validate_on_submit():
        course.title = form.title.data
        course.description = form.description.data
        course.instructor_id = form.instructor.data.id
        course.day_of_week = form.day_of_week.data
        course.start_time = form.start_time.data
        course.end_time = form.end_time.data
        course.capacity = form.capacity.data
        db.session.commit()
        flash('The course has been updated successfully!', 'success')
        return redirect(url_for('manage_courses'))

    elif request.method == 'GET':
        form.title.data = course.title
        form.description.data = course.description
        form.instructor.data = course.instructor
        form.day_of_week.data = course.day_of_week
        form.start_time.data = course.start_time
        form.end_time.data = course.end_time
        form.capacity.data = course.capacity

    return render_template('course_form.html', title='Edit Course', form=form, legend=f'ویرایش دوره: {course.title}')


@app.route('/course/<int:course_id>/delete', methods=['POST'])
@login_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)

    if current_user.role != 'admin' and course.instructor != current_user:
        abort(403)

    db.session.delete(course)
    db.session.commit()
    flash('The course has been deleted.', 'danger')
    return redirect(url_for('manage_courses'))


@app.route('/courses')
def courses():
    all_courses = Course.query.options(db.joinedload(Course.instructor)).order_by(Course.title).all()

    enrollment_counts = {
        enrollment.course_id: enrollment.count
        for enrollment in db.session.query(
            Enrollment.course_id, db.func.count(Enrollment.course_id).label('count')
        ).group_by(Enrollment.course_id).all()
    }


    student_enrollments_ids = []

    if current_user.is_authenticated and current_user.role == 'student':
        student_enrollments_ids = [
            e.course_id for e in Enrollment.query.filter_by(user_id=current_user.id).all()
        ]


    return render_template(
        'courses.html',
        title='Courses',
        courses=all_courses,
        enrollment_counts=enrollment_counts,
        student_enrollments_ids=student_enrollments_ids
    )

@app.route('/course/<int:course_id>')
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)

    enrollment_count = Enrollment.query.filter_by(course_id=course.id).count()
    remaining_capacity = course.capacity - enrollment_count
    return render_template(
        'course_detail.html',
        title=course.title,
        course=course,
        remaining_capacity=remaining_capacity
    )


@app.route('/enroll/<int:course_id>', methods=['POST'])
@login_required
def enroll(course_id):
    if current_user.role != "student":
        flash('Only students can enroll in courses.', 'warning')
        return redirect(url_for('courses'))

    course_to_enroll = Course.query.get_or_404(course_id)

    existing_enrollment = Enrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_to_enroll.id
    ).first()
    if existing_enrollment:
        flash('You are already enrolled in this course.', 'info')
        return redirect(url_for('courses'))

    enrolled_count = Enrollment.query.filter_by(course_id=course_to_enroll.id).count()
    if enrolled_count >= course_to_enroll.capacity:
        flash('This course is full.', 'danger')
        return redirect(url_for('course_detail', course_id=course_id))

    student_courses = Course.query.join(Enrollment).filter(Enrollment.user_id == current_user.id).all()
    for enrolled_course in student_courses:
        if enrolled_course.day_of_week == course_to_enroll.day_of_week:
            if (
                    enrolled_course.start_time < course_to_enroll.end_time and course_to_enroll.start_time < enrolled_course.end_time):
                flash(f'Time conflict with course: {enrolled_course.title}', 'danger')
                return redirect(url_for('course_detail', course_id=course_id))

    new_enrollment = Enrollment(user_id=current_user.id, course_id=course_to_enroll.id)
    db.session.add(new_enrollment)
    db.session.commit()
    flash(f'You have successfully enrolled in {course_to_enroll.title}!', 'success')
    return redirect(url_for('courses'))
