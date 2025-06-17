# file: app/routes.py (Final and Complete Version)

from flask import render_template, flash, redirect, url_for, request, abort
from flask_login import current_user, login_user, logout_user, login_required
from datetime import timedelta
import re
from app import app, db
from app.forms import (LoginForm, RegistrationForm, CourseForm,
                       EditProfileForm, TermForm)
from app.models import User, Course, Enrollment, Term


# =================================================================
# --- Main and Public Routes
# =================================================================

@app.route('/')
@app.route('/index')
def index():
    """Main entry point. Redirects guests to home and logged-in users to their dashboard."""
    if not current_user.is_authenticated:
        return render_template('home.html', title='خوش آمدید')
    return redirect(url_for('my_dashboard'))


@app.route('/home')
def home():
    """Homepage for guest users."""
    return render_template('home.html', title='خوش آمدید')


@app.route('/courses')
def courses():
    """Displays the list of available courses for the active term."""
    active_term = Term.query.filter_by(is_active=True).first()
    all_courses = []
    if not active_term:
        flash('در حال حاضر هیچ ترم فعالی برای ثبت‌نام وجود ندارد.', 'warning')
    else:
        all_courses = Course.query.filter_by(term_id=active_term.id).options(db.joinedload(Course.instructor)).order_by(
            Course.title).all()

    enrollment_counts = {
        e.course_id: e.count
        for e in db.session.query(
            Enrollment.course_id, db.func.count(Enrollment.course_id).label('count')
        ).group_by(Enrollment.course_id).all()
    }

    student_enrollments_ids = set()
    if current_user.is_authenticated and current_user.role == 'student':
        student_enrollments_ids = {e.course_id for e in current_user.enrollments}

    return render_template(
        'courses.html',
        title='لیست دوره‌ها',
        courses=all_courses,
        enrollment_counts=enrollment_counts,
        student_enrollments_ids=student_enrollments_ids,
        active_term=active_term
    )


@app.route('/course/<int:course_id>')
def course_detail(course_id):
    """Displays the full details for a single course."""
    course = Course.query.get_or_404(course_id)
    enrollment_count = Enrollment.query.filter_by(course_id=course.id).count()
    remaining_capacity = course.capacity - enrollment_count
    return render_template(
        'course_detail.html',
        title=course.title,
        course=course,
        remaining_capacity=remaining_capacity
    )


# =================================================================
# --- User Management and Profile Routes
# =================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('نام کاربری یا رمز عبور نامعتبر است.', 'danger')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        flash('شما با موفقیت وارد شدید!', 'success')
        return redirect(url_for('index'))
    return render_template('login.html', title='ورود', form=form)


@app.route('/logout')
@login_required
def logout():
    """Logs the user out."""
    logout_user()
    flash('شما با موفقیت از حساب خود خارج شدید.', 'info')
    return redirect(url_for('home'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """New user registration page."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('ثبت‌نام شما با موفقیت انجام شد! حالا می‌توانید وارد شوید.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='ثبت‌نام', form=form)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile editing page."""
    form = EditProfileForm(current_user.username, current_user.email)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        if form.password.data:
            current_user.set_password(form.password.data)
        db.session.commit()
        flash('تغییرات شما با موفقیت ذخیره شد.', 'success')
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template('profile.html', title='پروفایل من', form=form)


# =================================================================
# --- Student Dashboard and Enrollment Routes
# =================================================================
# file: app/routes.py (فقط تابع my_dashboard را با این نسخه جایگزین کنید)

# file: app/routes.py (فقط تابع my_dashboard را با این نسخه جایگزین کنید)

# ////////////////////////////////////
# file: app/routes.py (فقط تابع my_dashboard را با این نسخه جایگزین کنید)
# file: app/routes.py (فقط تابع my_dashboard را با این نسخه جایگزین کنید)

@app.route('/my_dashboard')
@login_required
def my_dashboard():
    """داشبورد اصلی کاربران با نمایش لیست دوره‌ها به تفکیک روز."""
    if current_user.role == 'student':
        # تمام دوره‌هایی که دانشجو ثبت‌نام کرده را بر اساس ساعت شروع مرتب می‌کنیم
        enrolled_courses = Course.query.join(Enrollment).filter(
            Enrollment.user_id == current_user.id
        ).order_by(Course.start_time).all()

        return render_template('dashboard.html', title='داشبورد من', courses=enrolled_courses)

    elif current_user.role in ['admin', 'instructor']:
        return redirect(url_for('manage_courses'))

    return redirect(url_for('index'))
# //////////////////////////////////////////
@app.route('/enroll/<int:course_id>', methods=['POST'])
@login_required
def enroll(course_id):
    """Handles the logic for a student enrolling in a course."""
    if current_user.role != "student":
        flash('فقط دانشجویان می‌توانند در دوره‌ها ثبت‌نام کنند.', 'warning')
        return redirect(url_for('courses'))

    course_to_enroll = Course.query.get_or_404(course_id)

    if not course_to_enroll.term.is_active:
        flash('ثبت‌نام برای این ترم بسته است.', 'warning')
        return redirect(url_for('courses'))

    existing_enrollment = Enrollment.query.filter_by(user_id=current_user.id, course_id=course_to_enroll.id).first()
    if existing_enrollment:
        flash('شما قبلاً در این دوره ثبت‌نام کرده‌اید.', 'info')
        return redirect(url_for('courses'))

    enrolled_count = Enrollment.query.filter_by(course_id=course_to_enroll.id).count()
    if enrolled_count >= course_to_enroll.capacity:
        flash('ظرفیت این دوره تکمیل است.', 'danger')
        return redirect(url_for('course_detail', course_id=course_id))

    required_prereqs = course_to_enroll.prereqs.all()
    if required_prereqs:
        completed_course_ids = {e.course_id for e in current_user.enrollments}
        for prereq in required_prereqs:
            if prereq.id not in completed_course_ids:
                flash(f'شما باید ابتدا درس پیشنیاز «{prereq.title}» را بگذرانید.', 'danger')
                return redirect(url_for('course_detail', course_id=course_id))

    student_courses_in_term = Course.query.join(Enrollment).filter(
        Enrollment.user_id == current_user.id,
        Course.term_id == course_to_enroll.term_id
    ).all()
    for enrolled_course in student_courses_in_term:
        if enrolled_course.day_of_week == course_to_enroll.day_of_week:
            if (
                    enrolled_course.start_time < course_to_enroll.end_time and course_to_enroll.start_time < enrolled_course.end_time):
                flash(f'تداخل زمانی با درس: {enrolled_course.title}', 'danger')
                return redirect(url_for('course_detail', course_id=course_id))

    new_enrollment = Enrollment(user_id=current_user.id, course_id=course_to_enroll.id)
    db.session.add(new_enrollment)
    db.session.commit()
    flash(f'شما با موفقیت در دوره {course_to_enroll.title} ثبت‌نام شدید!', 'success')
    return redirect(url_for('courses'))


@app.route('/unenroll/<int:course_id>', methods=['POST'])
@login_required
def unenroll(course_id):
    """Handles the logic for a student unenrolling from a course."""
    if current_user.role != 'student':
        abort(403)
    enrollment_to_delete = Enrollment.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    if enrollment_to_delete:
        db.session.delete(enrollment_to_delete)
        db.session.commit()
        flash('ثبت‌نام شما در این دوره با موفقیت لغو شد.', 'success')
    else:
        flash('رکورد ثبت‌نامی پیدا نشد.', 'danger')
    return redirect(url_for('my_dashboard'))


# =================================================================
# --- Administrative Routes (Admin / Instructor)
# =================================================================

@app.route('/admin/terms', methods=['GET', 'POST'])
@login_required
def manage_terms():
    """Term management page (Admin only)."""
    if current_user.role != 'admin':
        abort(403)
    form = TermForm()
    if form.validate_on_submit():
        if form.is_active.data:
            Term.query.update({'is_active': False}, synchronize_session=False)
        new_term = Term(name=form.name.data, is_active=form.is_active.data)
        db.session.add(new_term)
        db.session.commit()
        flash('ترم جدید با موفقیت ایجاد شد.', 'success')
        return redirect(url_for('manage_terms'))
    terms = Term.query.order_by(Term.id.desc()).all()
    return render_template('manage_terms.html', title='مدیریت ترم‌ها', form=form, terms=terms)


@app.route('/manage/courses')
@login_required
def manage_courses():
    """Course management panel for Admin and Instructor."""
    if current_user.role not in ['admin', 'instructor']:
        abort(403)
    if current_user.role == 'admin':
        courses = Course.query.order_by(Course.term_id.desc(), Course.title).all()
    else:  # Instructor
        courses = Course.query.filter_by(instructor_id=current_user.id).order_by(Course.term_id.desc(),
                                                                                 Course.title).all()
    return render_template('manage_courses.html', title='مدیریت دوره‌ها', courses=courses)


@app.route('/course/new', methods=['GET', 'POST'])
@login_required
def create_course():
    """Page for creating a new course."""
    if current_user.role not in ['admin', 'instructor']:
        abort(403)
    if not Term.query.first():
        flash('ابتدا باید حداقل یک ترم در سیستم تعریف کنید.', 'warning')
        return redirect(url_for('manage_terms'))
    form = CourseForm()
    if current_user.role == 'instructor' and request.method == 'GET':
        form.instructor.data = current_user
    if form.validate_on_submit():
        new_course = Course(
            title=form.title.data, description=form.description.data,
            instructor_id=form.instructor.data.id, term_id=form.term.data.id,
            day_of_week=form.day_of_week.data, start_time=form.start_time.data,
            end_time=form.end_time.data, capacity=form.capacity.data
        )
        new_course.prereqs = form.prereqs.data
        db.session.add(new_course)
        db.session.commit()
        flash('دوره جدید با موفقیت ایجاد شد!', 'success')
        return redirect(url_for('manage_courses'))
    return render_template('course_form.html', title='ایجاد دوره جدید', form=form, legend='ایجاد دوره جدید')


@app.route('/course/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    """Page for editing an existing course."""
    course = Course.query.get_or_404(course_id)
    if current_user.role != 'admin' and course.instructor_id != current_user.id:
        abort(403)
    form = CourseForm(obj=course)
    if form.validate_on_submit():
        form.populate_obj(course)
        # populate_obj does not handle many-to-many relationships well, so we do it manually.
        course.prereqs = form.prereqs.data
        db.session.commit()
        flash('دوره با موفقیت به‌روزرسانی شد!', 'success')
        return redirect(url_for('manage_courses'))
    elif request.method == 'GET':
        form.prereqs.data = course.prereqs.all()
    return render_template('course_form.html', title='ویرایش دوره', form=form, legend=f'ویرایش دوره: {course.title}')


@app.route('/course/<int:course_id>/delete', methods=['POST'])
@login_required
def delete_course(course_id):
    """Action to delete a course."""
    course = Course.query.get_or_404(course_id)
    if current_user.role != 'admin' and course.instructor_id != current_user.id:
        abort(403)
    Enrollment.query.filter_by(course_id=course.id).delete()
    # Also need to clear prerequisite relationships
    course.prereqs = []
    course.is_prereq_for = []
    db.session.commit()  # commit clearing relationships
    db.session.delete(course)
    db.session.commit()
    flash('دوره و تمام ثبت‌نامی‌های آن با موفقیت حذف شد.', 'danger')
    return redirect(url_for('manage_courses'))


@app.route('/course/<int:course_id>/roster')
@login_required
def course_roster(course_id):
    """Page to view the list of enrolled students in a course."""
    course = Course.query.get_or_404(course_id)
    if current_user.role != 'admin' and course.instructor_id != current_user.id:
        abort(403)
    students = [enrollment.student for enrollment in course.enrollments]
    return render_template('roster.html', title=f'دانشجویان دوره {course.title}', course=course, students=students)