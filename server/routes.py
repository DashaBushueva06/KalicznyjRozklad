from flask import current_app as app, render_template, request, redirect, url_for
from storage.db_repository import repository
from storage.excel_handler import excel_handler

@app.route('/')
def index(): # Головна сторінка (віддає HTML-меню сайту)
    return render_template('index.html')

@app.route('/<string:entity>/<int:item_id>/delete', methods=['POST'])
# Динамічно визначає таблицю за текстом з URL, видаляє запис із бази, оновлює Excel і повертає користувача назад
def generic_delete(entity, item_id):
    entity_map = { # Мапа відповідності: назва сутності в URL -> (об'єкт репозиторію, view-функція списку)
        'students': (repository.students, 'students_list'),
        'teachers': (repository.teachers, 'teachers_list'),
        'disciplines': (repository.disciplines, 'disciplines_list'),
        'classrooms': (repository.classrooms, 'classrooms_list'),
        'grades': (repository.grades, 'grades_list'),
        'schedules': (repository.schedules, 'schedule_list')
    }
    repo, redirect_view = entity_map.get(entity, (None, 'index')) # Дістаю потрібний репозиторій та ім'я функції для редиректу

    if repo:
        repo.delete(item_id)
        excel_handler.sync_all_data() # Після видалення ініціюю оновлення Excel-файлу

    return redirect(url_for(redirect_view))


# Студенти
@app.route('/students', methods=['GET'])
def students_list():
    students = repository.students.get_all()
    return render_template('students.html', students=students)

@app.route('/students/add', methods=['POST'])
def add_student():
    form_data = request.form.to_dict()  # Автоматично згортаю всі введені користувачем input форми в один словник
    if all(form_data.values()):  # Перевіряю на бекенді, чи всі поля моєї форми були заповнені
        repository.students.create(**form_data)  # Передаю пакунок даних форми для створення запису
        excel_handler.sync_all_data()
    return redirect(url_for('students_list'))


# Викладачі
@app.route('/teachers', methods=['GET'])
def teachers_list():
    teachers = repository.teachers.get_all()
    return render_template('teachers.html', teachers=teachers)

@app.route('/teachers/add', methods=['POST'])
def add_teacher():
    form_data = request.form.to_dict()
    if all(form_data.values()):
        repository.teachers.create(**form_data)
        excel_handler.sync_all_data()
    return redirect(url_for('teachers_list'))


# Дисципліни
@app.route('/disciplines', methods=['GET'])
def disciplines_list():
    disciplines = repository.get_disciplines_with_details()
    teachers = repository.teachers.get_all()
    return render_template('disciplines.html', disciplines=disciplines, teachers=teachers)

@app.route('/disciplines/add', methods=['POST'])
def add_discipline():
    title = request.form.get('title')
    teacher_id = request.form.get('teacher_id') # Текст із <select name="teacher_id"> прилітає як рядок, сервер конвертує в ID (int)

    if title and teacher_id:
        # Тут потрібна конвертація ForeignKey в ціле число (int)
        repository.disciplines.create(title=title, teacher_id=int(teacher_id))
        excel_handler.sync_all_data()

    return redirect(url_for('disciplines_list'))


#Аудиторії
@app.route('/classrooms', methods=['GET'])
def classrooms_list():
    classrooms = repository.classrooms.get_all()
    return render_template('classrooms.html', classrooms=classrooms)

@app.route('/classrooms/add', methods=['POST'])
def add_classroom():
    room_number = request.form.get('room_number')
    capacity = request.form.get('capacity')

    if room_number and capacity:
        # Конвертую місткість в int, бо база даних очікує числове значення для лічильника місць
        repository.classrooms.create(room_number=room_number, capacity=int(capacity))
        excel_handler.sync_all_data()

    return redirect(url_for('classrooms_list'))


# Оцінки
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
        repository.grades.create( # Перетворюю всі ID та саму оцінку на числа, щоб уникнути конфліктів
            student_id=int(student_id), # Сервер конвертує вибрані в інтерфейсі ID студента на числа
            discipline_id=int(discipline_id),
            value=int(value)
        )
        excel_handler.sync_all_data()

    return redirect(url_for('grades_list'))


# Розклад
@app.route('/schedule', methods=['GET'])
def schedule_list():
    schedules = repository.get_full_schedule()
    disciplines = repository.disciplines.get_all()
    classrooms = repository.classrooms.get_all()
    return render_template('schedule.html', schedules=schedules, disciplines=disciplines, classrooms=classrooms)

@app.route('/schedule/add', methods=['POST'])
def add_schedule():
    form_data = request.form.to_dict()

    if all(form_data.values()):
        form_data['discipline_id'] = int(form_data['discipline_id']) # Конвертую лише числові ідентифікатори, а текстові поля залишаю як є
        form_data['classroom_id'] = int(form_data['classroom_id'])
        repository.schedules.create(**form_data) # Передаю весь готовий та очищений словник у базу
        excel_handler.sync_all_data()

    return redirect(url_for('schedule_list'))