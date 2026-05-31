# Вміст: Опис усіх HTTP-ендпоінтів (/students, /grades/add тощо). Функції-обробники маршрутів приймають дані з HTML-форм (або JSON), здійснюють базову валідацію і викликають відповідні функції збереження.
#
# Зв'язки: Імпортує storage/db_repository.py та storage/excel_handler.py. Для виконання транзакції обробник викликає спочатку функцію БД, а потім функцію оновлення Excel. Якщо використовується Flask, імпортує функцію render_template.
#
# Експортується до: server/app.py.

"""
Модуль маршрутизації веб-сервера Flask.
Визначає кінцеві точки (endpoints) для виконання CRUD-операцій та виклику логіки синхронізації з Excel.
"""

from flask import current_app as app, render_template, request, redirect, url_for
from storage.db_repository import repository
from storage.excel_handler import excel_handler


@app.route('/')
def index():
    """Головна сторінка системи."""
    return render_template('index.html')


# ==========================================
# CRUD-операції: Студенти
# ==========================================

@app.route('/students', methods=['GET'])
def students_list():
    """Відображення списку студентів."""
    students = repository.students.get_all()
    return render_template('students.html', students=students)


@app.route('/students/add', methods=['POST'])
def add_student():
    """Обробка форми додавання нового студента."""
    name = request.form.get('name')
    group_id = request.form.get('group_id')

    if name and group_id:
        repository.students.create(name=name, group_id=group_id)
        excel_handler.sync_all_data()

    return redirect(url_for('students_list'))


@app.route('/students/<int:student_id>/delete', methods=['POST'])
def delete_student(student_id):
    """Видалення студента за ідентифікатором."""
    repository.students.delete(student_id)
    excel_handler.sync_all_data()
    return redirect(url_for('students_list'))


# ==========================================
# CRUD-операції: Викладачі
# ==========================================

@app.route('/teachers', methods=['GET'])
def teachers_list():
    """Відображення списку викладачів."""
    teachers = repository.teachers.get_all()
    return render_template('teachers.html', teachers=teachers)


@app.route('/teachers/add', methods=['POST'])
def add_teacher():
    """Обробка форми додавання нового викладача."""
    name = request.form.get('name')
    department = request.form.get('department')

    if name and department:
        repository.teachers.create(name=name, department=department)
        excel_handler.sync_all_data()

    return redirect(url_for('teachers_list'))


@app.route('/teachers/<int:teacher_id>/delete', methods=['POST'])
def delete_teacher(teacher_id):
    """Видалення викладача."""
    repository.teachers.delete(teacher_id)
    excel_handler.sync_all_data()
    return redirect(url_for('teachers_list'))


# ==========================================
# CRUD-операції: Курси
# ==========================================

@app.route('/courses', methods=['GET'])
def courses_list():
    """Відображення списку курсів із підтягуванням даних викладачів для форми."""
    # Використання жадібного завантаження для уникнення DetachedInstanceError
    courses = repository.get_courses_with_details()
    teachers = repository.teachers.get_all()
    return render_template('courses.html', courses=courses, teachers=teachers)

@app.route('/courses/add', methods=['POST'])
def add_course():
    """Обробка додавання курсу із прив'язкою зовнішнього ключа викладача."""
    title = request.form.get('title')
    teacher_id = request.form.get('teacher_id')

    if title and teacher_id:
        repository.courses.create(title=title, teacher_id=int(teacher_id))
        excel_handler.sync_all_data()

    return redirect(url_for('courses_list'))


@app.route('/courses/<int:course_id>/delete', methods=['POST'])
def delete_course(course_id):
    """Видалення курсу."""
    repository.courses.delete(course_id)
    excel_handler.sync_all_data()
    return redirect(url_for('courses_list'))


# ==========================================
# CRUD-операції: Аудиторії
# ==========================================

@app.route('/classrooms', methods=['GET'])
def classrooms_list():
    """Відображення списку аудиторій."""
    classrooms = repository.classrooms.get_all()
    return render_template('classrooms.html', classrooms=classrooms)


@app.route('/classrooms/add', methods=['POST'])
def add_classroom():
    """Реєстрація нової аудиторії."""
    building = request.form.get('building')
    room_number = request.form.get('room_number')
    capacity = request.form.get('capacity')

    if building and room_number and capacity:
        repository.classrooms.create(
            building=building,
            room_number=room_number,
            capacity=int(capacity)
        )
        excel_handler.sync_all_data()

    return redirect(url_for('classrooms_list'))


@app.route('/classrooms/<int:classroom_id>/delete', methods=['POST'])
def delete_classroom(classroom_id):
    """Видалення аудиторії."""
    repository.classrooms.delete(classroom_id)
    excel_handler.sync_all_data()
    return redirect(url_for('classrooms_list'))


# ==========================================
# CRUD-операції: Оцінки
# ==========================================

@app.route('/grades', methods=['GET'])
def grades_list():
    """Відображення відомості оцінок з використанням JOIN-запиту."""
    grades = repository.get_grades_with_details()
    students = repository.students.get_all()
    courses = repository.courses.get_all()
    return render_template('grades.html', grades=grades, students=students, courses=courses)


@app.route('/grades/add', methods=['POST'])
def add_grade():
    """Реєстрація оцінки для студента з певного курсу."""
    student_id = request.form.get('student_id')
    course_id = request.form.get('course_id')
    value = request.form.get('value')

    if student_id and course_id and value:
        repository.grades.create(
            student_id=int(student_id),
            course_id=int(course_id),
            value=int(value)
        )
        excel_handler.sync_all_data()

    return redirect(url_for('grades_list'))


@app.route('/grades/<int:grade_id>/delete', methods=['POST'])
def delete_grade(grade_id):
    """Анулювання оцінки."""
    repository.grades.delete(grade_id)
    excel_handler.sync_all_data()
    return redirect(url_for('grades_list'))


# ==========================================
# CRUD-операції: Розклад
# ==========================================

@app.route('/schedule', methods=['GET'])
def schedule_list():
    """Відображення розкладу із завантаженням пов'язаних сутностей."""
    schedules = repository.get_full_schedule()
    courses = repository.courses.get_all()
    classrooms = repository.classrooms.get_all()
    return render_template('schedule.html', schedules=schedules, courses=courses, classrooms=classrooms)


@app.route('/schedule/add', methods=['POST'])
def add_schedule():
    """Додавання нового запису до розкладу."""
    day_of_week = request.form.get('day_of_week')
    time_slot = request.form.get('time_slot')
    course_id = request.form.get('course_id')
    classroom_id = request.form.get('classroom_id')

    if day_of_week and time_slot and course_id and classroom_id:
        repository.schedules.create(
            day_of_week=day_of_week,
            time_slot=time_slot,
            course_id=int(course_id),
            classroom_id=int(classroom_id)
        )
        excel_handler.sync_all_data()

    return redirect(url_for('schedule_list'))


@app.route('/schedule/<int:schedule_id>/delete', methods=['POST'])
def delete_schedule(schedule_id):
    """Видалення запису з розкладу."""
    repository.schedules.delete(schedule_id)
    excel_handler.sync_all_data()
    return redirect(url_for('schedule_list'))