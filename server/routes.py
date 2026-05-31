from flask import current_app as app, render_template, request, redirect, url_for
from storage.db_repository import repository
from storage.excel_handler import excel_handler


@app.route('/')
def index():
    return render_template('index.html')


# --- Студенти ---
@app.route('/students', methods=['GET'])
def students_list():
    students = repository.students.get_all()
    return render_template('students.html', students=students)


@app.route('/students/add', methods=['POST'])
def add_student():
    name = request.form.get('name')
    specialization = request.form.get('specialization')
    course = request.form.get('course')

    if name and specialization and course:
        repository.students.create(name=name, specialization=specialization, course=course)
        excel_handler.sync_all_data()

    return redirect(url_for('students_list'))


@app.route('/students/<int:student_id>/delete', methods=['POST'])
def delete_student(student_id):
    repository.students.delete(student_id)
    excel_handler.sync_all_data()
    return redirect(url_for('students_list'))


# --- Викладачі ---
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


# --- Дисципліни ---
@app.route('/disciplines', methods=['GET'])
def disciplines_list():
    # ОЦЕЙ РЯДОК МИ ВИПРАВИЛИ (тепер тут get_disciplines_with_details):
    disciplines = repository.get_disciplines_with_details()
    teachers = repository.teachers.get_all()
    return render_template('disciplines.html', disciplines=disciplines, teachers=teachers)


@app.route('/disciplines/add', methods=['POST'])
def add_discipline():
    title = request.form.get('title')
    teacher_id = request.form.get('teacher_id')

    if title and teacher_id:
        repository.disciplines.create(title=title, teacher_id=int(teacher_id))
        excel_handler.sync_all_data()

    return redirect(url_for('disciplines_list'))


@app.route('/disciplines/<int:discipline_id>/delete', methods=['POST'])
def delete_discipline(discipline_id):
    repository.disciplines.delete(discipline_id)
    excel_handler.sync_all_data()
    return redirect(url_for('disciplines_list'))


# --- Аудиторії ---
@app.route('/classrooms', methods=['GET'])
def classrooms_list():
    classrooms = repository.classrooms.get_all()
    return render_template('classrooms.html', classrooms=classrooms)


@app.route('/classrooms/add', methods=['POST'])
def add_classroom():
    # Прибрали параметр building
    room_number = request.form.get('room_number')
    capacity = request.form.get('capacity')

    if room_number and capacity:
        # Передаємо в базу тільки номер та місткість
        repository.classrooms.create(
            room_number=room_number,
            capacity=int(capacity)
        )
        excel_handler.sync_all_data()

    return redirect(url_for('classrooms_list'))


@app.route('/classrooms/<int:classroom_id>/delete', methods=['POST'])
def delete_classroom(classroom_id):
    repository.classrooms.delete(classroom_id)
    excel_handler.sync_all_data()
    return redirect(url_for('classrooms_list'))

# --- Оцінки ---
@app.route('/grades', methods=['GET'])
def grades_list():
    grades = repository.get_grades_with_details()
    students = repository.students.get_all()
    disciplines = repository.disciplines.get_all()
    return render_template('grades.html', grades=grades, students=students, disciplines=disciplines)


@app.route('/grades/add', methods=['POST'])
def add_grade():
    student_id = request.form.get('student_id')
    discipline_id = request.form.get('discipline_id')
    value = request.form.get('value')

    if student_id and discipline_id and value:
        repository.grades.create(
            student_id=int(student_id),
            discipline_id=int(discipline_id),
            value=int(value)
        )
        excel_handler.sync_all_data()

    return redirect(url_for('grades_list'))


@app.route('/grades/<int:grade_id>/delete', methods=['POST'])
def delete_grade(grade_id):
    repository.grades.delete(grade_id)
    excel_handler.sync_all_data()
    return redirect(url_for('grades_list'))


# --- Розклад ---
@app.route('/schedule', methods=['GET'])
def schedule_list():
    schedules = repository.get_full_schedule()
    disciplines = repository.disciplines.get_all()
    classrooms = repository.classrooms.get_all()
    return render_template('schedule.html', schedules=schedules, disciplines=disciplines, classrooms=classrooms)


@app.route('/schedule/add', methods=['POST'])
def add_schedule():
    day_of_week = request.form.get('day_of_week')
    time_slot = request.form.get('time_slot')
    discipline_id = request.form.get('discipline_id')
    classroom_id = request.form.get('classroom_id')
    specialization = request.form.get('specialization')  # Приймаємо спеціальність
    course = request.form.get('course')                  # Приймаємо курс

    if day_of_week and time_slot and discipline_id and classroom_id and specialization and course:
        repository.schedules.create(
            day_of_week=day_of_week,
            time_slot=time_slot,
            discipline_id=int(discipline_id),
            classroom_id=int(classroom_id),
            specialization=specialization,
            course=course
        )
        excel_handler.sync_all_data()

    return redirect(url_for('schedule_list'))