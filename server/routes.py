# Вміст: Обробка HTTP-запитів (GET та POST), маршрутизація веб-сторінок системи, зчитування даних із веб-форм, виклик методів репозиторію для зміни стану БД та запуск двосторонньої синхронізації з Excel.
#
# Зв'язки:
#   1. Імпортує глобальний об'єкт додатка через current_app для реєстрації маршрутів.
#   2. Імпортує database/db_repository.py для виконання CRUD-операцій з моделями.
#   3. Імпортує модуль storage/excel_handler.py для вивантаження оновлених даних назад в Excel.
#
# Експортується до: Динамічно завантажується всередину функції у файлі server/app.py за умови активованого контексту.

from flask import current_app as app, render_template, request, redirect, url_for
from storage.db_repository import repository
from storage.excel_handler import excel_handler


@app.route('/')
def index():
    return render_template('index.html')


# --- Студенти ---

# Маршрут для перегляду списку студентів (приймає тільки безпечні GET-запити)
@app.route('/students', methods=['GET'])
def students_list():
    # Запитуємо у репозиторію список усіх студентів, які зараз є в базі даних
    students = repository.students.get_all()
    # Передаємо цей список у HTML-шаблон для відмальовки таблиці на екрані
    return render_template('students.html', students=students)


# Маршрут для обробки форми додавання нового студента (приймає POST-запити з даними)
@app.route('/students/add', methods=['POST'])
def add_student():
    # Витягуємо текстові значення, які користувач ввів у поля веб-форми
    name = request.form.get('name')
    specialization = request.form.get('specialization')
    course = request.form.get('course')

    # Валідація: перевіряємо, що користувач не відправив пусті поля
    if name and specialization and course:
        # Даємо команду репозиторію створити новий рядок у таблиці студентів
        repository.students.create(name=name, specialization=specialization, course=course)
        # Одразу вивантажуємо оновлені дані з бази в Excel-файл для синхронізації
        excel_handler.sync_all_data()

    # Перенаправляємо браузер користувача назад на сторінку зі списком студентів
    return redirect(url_for('students_list'))


# Маршрут для видалення студента за його унікальним ID (приймає POST-запит)
@app.route('/students/<int:student_id>/delete', methods=['POST'])
def delete_student(student_id):
    # Викликаємо метод репозиторію для видалення запису з бази за його первинним ключем
    repository.students.delete(student_id)
    # Перезаписуємо Excel-файл, щоб видалити студента і звідти
    excel_handler.sync_all_data()
    # Оновлюємо сторінку користувача через перенаправлення на список студентів
    return redirect(url_for('students_list'))


# --- Викладачі ---

# Маршрут для відображення сторінки з таблицею всіх викладачів (безпечне читання даних)
@app.route('/teachers', methods=['GET'])
def teachers_list():
    """Відображення списку викладачів."""
    # Запитуємо у репозиторію повний перелік викладачів із бази SQLite
    teachers = repository.teachers.get_all()
    # Завантажуємо HTML-шаблон та передаємо туди список для відображення
    return render_template('teachers.html', teachers=teachers)


# Маршрут для прийому даних із форми та створення нового викладача в системі
@app.route('/teachers/add', methods=['POST'])
def add_teacher():
    """Обробка форми додавання нового викладача."""
    # Зчитуємо текстові дані з полів форми (ПІБ та Кафедра викладача)
    name = request.form.get('name')
    department = request.form.get('department')

    # Якщо обидва поля заповнені — виконуємо збереження
    if name and department:
        # Створюємо новий запис у таблиці викладачів через репозиторій
        repository.teachers.create(name=name, department=department)
        # Оновлюємо копію даних у файлі Excel, щоб зберегти синхронізацію
        excel_handler.sync_all_data()

    # Повертаємо користувача на оновлений список викладачів (захист від дублювання F5)
    return redirect(url_for('teachers_list'))


# Маршрут для видалення викладача, де його ID динамічно передається прямо в адресі сторінки
@app.route('/teachers/<int:teacher_id>/delete', methods=['POST'])
def delete_teacher(teacher_id):
    """Видалення викладача."""
    # Видаляємо запис про викладача з бази за його унікальним номером ID
    repository.teachers.delete(teacher_id)
    # Запускаємо синхронізацію, щоб викреслити цього викладача і з Excel-файлу
    excel_handler.sync_all_data()
    # Перенаправляємо браузер користувача назад на сторінку списку викладачів
    return redirect(url_for('teachers_list'))


# --- Дисципліни ---

# Сторінка перегляду всіх предметів (GET-запит)
@app.route('/disciplines', methods=['GET'])
def disciplines_list():
    # Завантажуємо предмети разом із ПІБ викладачів за 1 запит (оптимізація JOIN)
    disciplines = repository.get_disciplines_with_details()
    # Беремо список усіх викладачів, щоб заповнити випадаючий список у формі на сайті
    teachers = repository.teachers.get_all()
    # Передаємо ці дані в HTML-шаблон для виведення на екран
    return render_template('disciplines.html', disciplines=disciplines, teachers=teachers)


# Обробка додавання нового предмету (POST-запит)
@app.route('/disciplines/add', methods=['POST'])
def add_discipline():
    # Зчитуємо з форми назву предмету та ID обраного зі списку викладача
    title = request.form.get('title')
    teacher_id = request.form.get('teacher_id')

    # Перевіряємо, що користувач заповнив обидва поля
    if title and teacher_id:
        # Зберігаємо предмет у базі, примусово переводячи текстовий ID викладача в число (int)
        repository.disciplines.create(title=title, teacher_id=int(teacher_id))
        # Оновлюємо файл Excel актуальними даними з бази
        excel_handler.sync_all_data()

    # Перенаправляємо користувача назад на список предметів (захист від дублів при оновленні F5)
    return redirect(url_for('disciplines_list'))


# Видалення предмету за його унікальним ID (POST-запит)
@app.route('/disciplines/<int:discipline_id>/delete', methods=['POST'])
def delete_discipline(discipline_id):
    # Видаляємо рядок дисципліни з бази даних SQLite за її первинним ключем
    repository.disciplines.delete(discipline_id)
    # Викреслюємо цю ж дисципліну з файлу Excel
    excel_handler.sync_all_data()
    # Перевантажуємо сторінку через редирект на список дисциплін
    return redirect(url_for('disciplines_list'))


# --- Аудиторії ---

# Сторінка перегляду всіх аудиторій (GET-запит)
@app.route('/classrooms', methods=['GET'])
def classrooms_list():
    # Запитуємо у репозиторію список усіх наявних кімнат/аудиторій
    classrooms = repository.classrooms.get_all()
    # Передаємо список в HTML для відмальовки таблиці
    return render_template('classrooms.html', classrooms=classrooms)


# Обробка додавання нової аудиторії (POST-запит)
@app.route('/classrooms/add', methods=['POST'])
def add_classroom():
    # Зчитуємо номер аудиторії та її місткість (скільки студентів поміститься)
    room_number = request.form.get('room_number')
    capacity = request.form.get('capacity')

    # Перевіряємо наявність даних у полях
    if room_number and capacity:
        # Створюємо запис у базі (параметр корпусу building повністю видалено зі структури)
        repository.classrooms.create(
            room_number=room_number,
            capacity=int(capacity)
        )
        # Синхронізуємо зміни з файлом Excel
        excel_handler.sync_all_data()

    # Повертаємо користувача на оновлений список аудиторій
    return redirect(url_for('classrooms_list'))


# Видалення аудиторії за її ID (POST-запит)
@app.route('/classrooms/<int:classroom_id>/delete', methods=['POST'])
def delete_classroom(classroom_id):
    # Стираємо аудиторію з бази даних
    repository.classrooms.delete(classroom_id)
    # Прибираємо її з файлу Excel
    excel_handler.sync_all_data()
    # Перенаправляємо браузер назад на сторінку аудиторій
    return redirect(url_for('classrooms_list'))


# --- Оцінки ---

# Сторінка перегляду журналу оцінок (GET-запит)
@app.route('/grades', methods=['GET'])
def grades_list():
    # Оптимізовано: дістаємо оцінки разом із ПІБ студентів та назвами предметів за один JOIN
    grades = repository.get_grades_with_details()
    # Беремо повні списки студентів та предметів для випадаючих меню у формі додавання
    students = repository.students.get_all()
    disciplines = repository.disciplines.get_all()
    # Передаємо весь цей набір даних у шаблон журналу оцінок
    return render_template('grades.html', grades=grades, students=students, disciplines=disciplines)


# Обробка виставлення нової оцінки (POST-запит)
@app.route('/grades/add', methods=['POST'])
def add_grade():
    # Зчитуємо ID студента, ID предмету та виставлений бал
    student_id = request.form.get('student_id')
    discipline_id = request.form.get('discipline_id')
    value = request.form.get('value')

    # Перевіряємо, що всі три параметри успішно прийшли з форми
    if student_id and discipline_id and value:
        # Пов'язуємо сутності: створюємо оцінку, конвертуючи всі ID та бал у цілі числа (int)
        repository.grades.create(
            student_id=int(student_id),
            discipline_id=int(discipline_id),
            value=int(value)
        )
        # Записуємо нову оцінку у файл Excel для повної синхронізації
        excel_handler.sync_all_data()

    # Перенаправляємо користувача на сторінку оновленого журналу оцінок
    return redirect(url_for('grades_list'))


# Видалення оцінки за її ID (POST-запит)
@app.route('/grades/<int:grade_id>/delete', methods=['POST'])
def delete_grade(grade_id):
    # Видаляємо запис про оцінку з бази
    repository.grades.delete(grade_id)
    # Синхронізуємо зміни, видаляючи цей рядок з Excel-таблиці
    excel_handler.sync_all_data()
    # Оновлюємо сторінку журналу через редирект
    return redirect(url_for('grades_list'))

# --- Розклад ---

# Сторінка перегляду загального розкладу занять (GET-запит)
@app.route('/schedule', methods=['GET'])
def schedule_list():
    # Завантажуємо розклад разом із дисциплінами, викладачами та аудиторіями за один оптимізований JOIN-запит
    schedules = repository.get_full_schedule()
    # Дістаємо предмети та аудиторії, щоб заповнити випадаючі меню у формі додавання пари
    disciplines = repository.disciplines.get_all()
    classrooms = repository.classrooms.get_all()
    # Передаємо всі зібрані дані в HTML-шаблон для виведення сітки розкладу
    return render_template('schedule.html', schedules=schedules, disciplines=disciplines, classrooms=classrooms)


# Обробка форми створення нового запису в розкладі (POST-запит)
@app.route('/schedule/add', methods=['POST'])
def add_schedule():
    # Зчитуємо параметри часу, місця та предмету
    day_of_week = request.form.get('day_of_week')
    time_slot = request.form.get('time_slot')
    discipline_id = request.form.get('discipline_id')
    classroom_id = request.form.get('classroom_id')
    specialization = request.form.get('specialization')
    course = request.form.get('course')

    # Перевіряємо, чи користувач заповнив абсолютно всі поля форми розкладу
    if day_of_week and time_slot and discipline_id and classroom_id and specialization and course:
        # Даємо команду репозиторію внести новий запис, конвертуючи ключі предмету та аудиторії в числа
        repository.schedules.create(
            day_of_week=day_of_week,
            time_slot=time_slot,
            discipline_id=int(discipline_id),
            classroom_id=int(classroom_id),
            specialization=specialization,
            course=course
        )
        # Синхронізуємо новий розклад із файлом Excel, переписуючи його актуальними даними
        excel_handler.sync_all_data()

    # Перенаправляємо користувача назад на оновлену сторінку розкладу занять
    return redirect(url_for('schedule_list'))