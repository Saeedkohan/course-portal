from flask import render_template, flash, redirect, url_for, request, abort
from flask_login import current_user, login_user, logout_user, login_required
from datetime import timedelta
import re
from sqlalchemy import func, desc

from app import app, db
from app.forms import (LoginForm, CourseForm, EditProfileForm, TermForm,
                       GradeForm, AdminCreateUserForm, ChangeRoleForm)
from app.models import User, Course, Enrollment, Term

@app.route('/')
@app.route('/index')
def index():
    if not current_user.is_authenticated:
        return render_template('home.html', title='خوش آمدید')
    return redirect(url_for('my_dashboard'))

@app.route('/home')
def home():
    return render_template('home.html', title='خوش آمدید')

@app.route('/courses')
def courses():
    page = request.args.get('page', 1, type=int)
    active_term = Term.query.filter_by(is_active=True).first()
    pagination = None
    if not active_term:
        flash('در حال حاضر هیچ ترم فعالی برای ثبت‌نام وجود ندارد.', 'warning')
        all_courses = []
    else:
        pagination = Course.query.filter_by(term_id=active_term.id).options(db.joinedload(Course.instructor)).order_by(Course.title).paginate(page=page, per_page=6, error_out=False)
        all_courses = pagination.items
    enrollment_counts = {e.course_id: e.count for e in db.session.query(Enrollment.course_id, func.count(Enrollment.course_id).label('count')).group_by(Enrollment.course_id).all()}
    student_enrollments_ids = {e.course_id for e in current_user.enrollments} if current_user.is_authenticated and current_user.role == 'student' else set()
    return render_template('courses.html', title='لیست دوره‌ها', pagination=pagination, courses=all_courses, enrollment_counts=enrollment_counts, student_enrollments_ids=student_enrollments_ids, active_term=active_term)

@app.route('/course/<int:course_id>')
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    enrollment_count = Enrollment.query.filter_by(course_id=course.id).count()
    remaining_capacity = course.capacity - enrollment_count
    return render_template('course_detail.html', title=course.title, course=course, remaining_capacity=remaining_capacity)

@app.route('/login', methods=['GET', 'POST'])
def login():
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
    logout_user()
    flash('شما با موفقیت از حساب خود خارج شدید.', 'info')
    return redirect(url_for('home'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
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

@app.route('/my_dashboard')
@login_required
def my_dashboard():
    if current_user.role == 'student':
        enrolled_courses = Course.query.join(Enrollment).filter(Enrollment.user_id == current_user.id).join(Term).order_by(Term.name.desc(), Course.start_time).all()
        return render_template('dashboard.html', title='داشبورد من', courses=enrolled_courses)
    elif current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'instructor':
        return redirect(url_for('manage_courses'))
    return redirect(url_for('index'))

@app.route('/transcript')
@login_required
def transcript():
    if current_user.role != 'student':
        abort(403)
    student_enrollments = Enrollment.query.filter_by(user_id=current_user.id).join(Course).join(Term).order_by(Term.name.desc(), Course.title).all()
    total_grade_points, total_credits, gpa = 0, 0, 0.0
    for enrollment in student_enrollments:
        if enrollment.grade is not None and enrollment.course.credits is not None:
            total_grade_points += enrollment.grade * enrollment.course.credits
            total_credits += enrollment.course.credits
    if total_credits > 0:
        gpa = total_grade_points / total_credits
    return render_template('transcript.html', title='کارنامه تحصیلی', enrollments=student_enrollments, total_credits=total_credits, gpa=gpa)

@app.route('/enroll/<int:course_id>', methods=['POST'])
@login_required
def enroll(course_id):
    if current_user.role != "student":
        flash('فقط دانشجویان می‌توانند در دوره‌ها ثبت‌نام کنند.', 'warning')
        return redirect(url_for('courses'))
    course_to_enroll = Course.query.get_or_404(course_id)
    if not course_to_enroll.term.is_active:
        flash('ثبت‌نام برای این ترم بسته است.', 'warning')
        return redirect(url_for('courses'))
    if Enrollment.query.filter_by(user_id=current_user.id, course_id=course_to_enroll.id).first():
        flash('شما قبلاً در این دوره ثبت‌نام کرده‌اید.', 'info')
        return redirect(url_for('courses'))
    if Enrollment.query.filter_by(course_id=course_to_enroll.id).count() >= course_to_enroll.capacity:
        flash('ظرفیت این دوره تکمیل است.', 'danger')
        return redirect(url_for('course_detail', course_id=course_id))
    required_prereqs = course_to_enroll.prereqs.all()
    if required_prereqs:
        completed_course_ids = {e.course_id for e in current_user.enrollments if e.grade is not None and e.grade >= 10}
        for prereq in required_prereqs:
            if prereq.id not in completed_course_ids:
                flash(f'شما باید ابتدا درس پیشنیاز «{prereq.title}» را بگذرانید.', 'danger')
                return redirect(url_for('course_detail', course_id=course_id))
    student_courses_in_term = Course.query.join(Enrollment).filter(Enrollment.user_id == current_user.id, Course.term_id == course_to_enroll.term_id).all()
    for enrolled_course in student_courses_in_term:
        if enrolled_course.day_of_week == course_to_enroll.day_of_week and (enrolled_course.start_time < course_to_enroll.end_time and course_to_enroll.start_time < enrolled_course.end_time):
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
    enrollment_to_delete = Enrollment.query.filter_by(user_id=current_user.id, course_id=course_id).first_or_404()
    if current_user.role != 'student':
        abort(403)
    db.session.delete(enrollment_to_delete)
    db.session.commit()
    flash('ثبت‌نام شما در این دوره با موفقیت لغو شد.', 'success')
    return redirect(url_for('my_dashboard'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        abort(403)
    student_count = User.query.filter_by(role='student').count()
    instructor_count = User.query.filter_by(role='instructor').count()
    course_count = Course.query.count()
    term_count = Term.query.count()
    return render_template('admin_dashboard.html', title='داشبورد مدیریت', student_count=student_count, instructor_count=instructor_count, course_count=course_count, term_count=term_count)

@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if current_user.role != 'admin':
        abort(403)
    create_form = AdminCreateUserForm()
    if create_form.submit_create.data and create_form.validate_on_submit():
        user = User(username=create_form.username.data, email=create_form.email.data, role=create_form.role.data)
        user.set_password(create_form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('کاربر جدید با موفقیت ایجاد شد.', 'success')
        return redirect(url_for('manage_users'))
    page = request.args.get('page', 1, type=int)
    users_pagination = User.query.order_by(User.id).paginate(page=page, per_page=10, error_out=False)
    return render_template('manage_users.html', title='مدیریت کاربران', users_pagination=users_pagination, form=create_form, ChangeRoleForm=ChangeRoleForm)

@app.route('/admin/user/<int:user_id>/set_role', methods=['POST'])
@login_required
def set_user_role(user_id):
    if current_user.role != 'admin':
        abort(403)
    user = User.query.get_or_404(user_id)
    form = ChangeRoleForm()
    if form.submit_change.data and form.validate_on_submit():
        if user.id == current_user.id:
            flash('شما نمی‌توانید نقش خودتان را تغییر دهید.', 'danger')
        else:
            user.role = form.role.data
            db.session.commit()
            flash(f'نقش کاربر «{user.username}» با موفقیت به‌روزرسانی شد.', 'success')
    return redirect(url_for('manage_users', page=request.args.get('page', 1, type=int)))

@app.route('/admin/terms', methods=['GET', 'POST'])
@login_required
def manage_terms():
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

@app.route('/term/<int:term_id>/activate', methods=['POST'])
@login_required
def activate_term(term_id):
    if current_user.role != 'admin':
        abort(403)
    Term.query.update({'is_active': False}, synchronize_session=False)
    term_to_activate = Term.query.get_or_404(term_id)
    term_to_activate.is_active = True
    db.session.commit()
    flash(f'ترم «{term_to_activate.name}» با موفقیت فعال شد.', 'success')
    return redirect(url_for('manage_terms'))

@app.route('/term/<int:term_id>/deactivate', methods=['POST'])
@login_required
def deactivate_term(term_id):
    if current_user.role != 'admin':
        abort(403)
    term_to_deactivate = Term.query.get_or_404(term_id)
    term_to_deactivate.is_active = False
    db.session.commit()
    flash(f'ترم «{term_to_deactivate.name}» با موفقیت غیرفعال شد.', 'warning')
    return redirect(url_for('manage_terms'))

@app.route('/manage/courses')
@login_required
def manage_courses():
    if current_user.role != 'admin':
        abort(403)
    courses = Course.query.order_by(Course.term_id.desc(), Course.title).all()
    return render_template('manage_courses.html', title='مدیریت دوره‌ها', courses=courses)

@app.route('/course/new', methods=['GET', 'POST'])
@login_required
def create_course():
    if current_user.role != 'admin':
        abort(403)
    if not Term.query.first():
        flash('ابتدا باید حداقل یک ترم در سیستم تعریف کنید.', 'warning')
        return redirect(url_for('manage_terms'))
    form = CourseForm()
    if form.validate_on_submit():
        new_course = Course(
            title=form.title.data, description=form.description.data,
            instructor_id=form.instructor.data.id, term_id=form.term.data.id,
            credits=form.credits.data, day_of_week=form.day_of_week.data,
            start_time=form.start_time.data, end_time=form.end_time.data,
            capacity=form.capacity.data)
        new_course.prereqs = form.prereqs.data
        db.session.add(new_course)
        db.session.commit()
        flash('دوره جدید با موفقیت ایجاد شد!', 'success')
        return redirect(url_for('manage_courses'))
    return render_template('course_form.html', title='ایجاد دوره جدید', form=form, legend='ایجاد دوره جدید')

@app.route('/course/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    if current_user.role != 'admin':
        abort(403)
    form = CourseForm(obj=course)
    if form.validate_on_submit():
        form.populate_obj(course)
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
    course = Course.query.get_or_404(course_id)
    if current_user.role != 'admin':
        abort(403)
    Enrollment.query.filter_by(course_id=course.id).delete()
    course.prereqs = []
    course.is_prereq_for = []
    db.session.commit()
    db.session.delete(course)
    db.session.commit()
    flash('دوره و تمام ثبت‌نامی‌های آن با موفقیت حذف شد.', 'danger')
    return redirect(url_for('manage_courses'))

@app.route('/course/<int:course_id>/roster')
@login_required
def course_roster(course_id):
    course = Course.query.get_or_404(course_id)
    if current_user.role != 'admin' and course.instructor_id != current_user.id:
        abort(403)
    enrollments = Enrollment.query.filter_by(course_id=course.id).all()
    grade_form = GradeForm()
    return render_template('roster.html', title=f'دانشجویان دوره {course.title}', course=course, enrollments=enrollments, grade_form=grade_form)

@app.route('/enrollment/<int:enrollment_id>/grade', methods=['POST'])
@login_required
def grade_enrollment(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    course = enrollment.course
    if current_user.role != 'admin' and course.instructor_id != current_user.id:
        abort(403)
    form = GradeForm()
    if form.validate_on_submit():
        enrollment.grade = form.grade.data
        enrollment.status = 'completed'
        db.session.commit()
        flash(f'نمره برای دانشجو {enrollment.student.username} با موفقیت ثبت شد.', 'success')
    else:
        if form.grade.errors:
            flash(f'خطا در ثبت نمره: {form.grade.errors[0]}', 'danger')
    return redirect(url_for('course_roster', course_id=course.id))

@app.route('/admin/reports')
@login_required
def admin_reports():
    if current_user.role != 'admin':
        abort(403)
    student_count = User.query.filter_by(role='student').count()
    instructor_count = User.query.filter_by(role='instructor').count()
    course_count = Course.query.count()
    term_count = Term.query.count()
    popular_courses = db.session.query(Course.title, func.count(Enrollment.id).label('enrollment_count')).join(Enrollment).group_by(Course.id).order_by(desc('enrollment_count')).limit(5).all()
    return render_template('reports.html', title='گزارشات سیستم', student_count=student_count, instructor_count=instructor_count, course_count=course_count, term_count=term_count, popular_courses=popular_courses)