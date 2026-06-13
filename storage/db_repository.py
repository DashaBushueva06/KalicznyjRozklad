# Вміст: Реалізація патерну Repository для інкапсуляції CRUD-операцій з базою даних, оптимізація складних реляційних запитів за допомогою жадібного завантаження (joinedload), та логіка розумного пакетного імпорту даних з Excel.
#
# Зв'язки:
#   1. Імпортує фабрику сесій SessionLocal з файла database/connection.py.
#   2. Імпортує класи-моделі (Student, Teacher тощо) з файла database/models.py.
#
# Експортується до: server/routes.py (для обробки дій на сторінках сайту) та main.py (для початкового заповнення бази з Excel при старті).

from typing import List, Optional, Type
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from database.connection import SessionLocal
from database.models import Base, Student, Teacher, Discipline, Classroom, Grade, Schedule


class BaseRepository:
    """Базовий клас репозиторію для стандартних CRUD-операцій."""

    def __init__(self, model: Type[Base]):
        # Приймаємо конкретну модель (наприклад, Student), з якою буде працювати цей екземпляр
        self.model = model

    def get_all(self) -> List[Base]:
        # Відкриваємо безпечну сесію; після виходу з блоку with вона закриється сама
        with SessionLocal() as session:
            # Повертаємо список усіх рядків цієї таблиці
            return session.query(self.model).all()

    def get_by_id(self, record_id: int) -> Optional[Base]:
        with SessionLocal() as session:
            # Шукаємо рядок за його унікальним цифровим ID
            return session.query(self.model).filter(self.model.id == record_id).first()

    def create(self, **kwargs) -> Base:
        with SessionLocal() as session:
            try:
                # Розпаковуємо отримані змінні (наприклад, name='Аня') і створюємо об'єкт
                new_record = self.model(**kwargs)
                session.add(new_record)      # Додаємо в чернетку сесії
                session.commit()             # Фізично зберігаємо в базу даних SQLite
                session.refresh(new_record)  # Оновлюємо об'єкт, щоб прочитати його новий ID
                return new_record
            except SQLAlchemyError as e:
                session.rollback()           # Якщо помилка — скасовуємо всі зміни в сесії
                raise RuntimeError(f"Помилка створення запису в {self.model.__tablename__}: {e}")

    def update(self, record_id: int, **kwargs) -> Optional[Base]:
        with SessionLocal() as session:
            try:
                # Знаходимо потрібний рядок для оновлення
                record = session.query(self.model).filter(self.model.id == record_id).first()
                if not record:
                    return None

                # Проходимо по всіх надісланих полях і міняємо їх у записі, якщо такі поля є
                for key, value in kwargs.items():
                    if hasattr(record, key):
                        setattr(record, key, value)

                session.commit()             # Зберігаємо зміни
                session.refresh(record)
                return record
            except SQLAlchemyError as e:
                session.rollback()           # Якщо помилка — скасовуємо всі зміни в сесії
                raise RuntimeError(f"Помилка оновлення запису в {self.model.__tablename__}: {e}")

    def delete(self, record_id: int) -> bool:
        with SessionLocal() as session:
            try:
                # Шукаємо запис, який користувач хоче видалити
                record = session.query(self.model).filter(self.model.id == record_id).first()
                if not record:
                    return False
                session.delete(record)       # Маркуємо запис як видалений
                session.commit()             # Фізично стираємо рядок із файлу бази
                return True
            except SQLAlchemyError as e:
                session.rollback()           # Якщо помилка — скасовуємо всі зміни в сесії
                raise RuntimeError(f"Помилка видалення запису з {self.model.__tablename__}: {e}")

class UniversityRepository:
    """Спеціалізований репозиторій для конкретних сутностей предметної області."""

    def __init__(self):
        # Налаштовуємо окремі репозиторії-роботи для кожної нашої таблиці
        self.students = BaseRepository(Student)
        self.teachers = BaseRepository(Teacher)
        self.disciplines = BaseRepository(Discipline)
        self.classrooms = BaseRepository(Classroom)
        self.grades = BaseRepository(Grade)
        self.schedules = BaseRepository(Schedule)

    def get_grades_with_details(self) -> List[Grade]:
        with SessionLocal() as session:
            # Оптимізація: за один JOIN-запит дістаємо оцінки разом із ПІБ студента та назвою предмету
            return session.query(Grade) \
                .options(joinedload(Grade.student), joinedload(Grade.discipline)) \
                .all()

    def get_student_grades(self, student_id: int) -> List[Grade]:
        with SessionLocal() as session:
            # Дістаємо оцінки конкретного студента за його ID разом із назвами дисциплін
            return session.query(Grade) \
                .options(joinedload(Grade.discipline)) \
                .filter(Grade.student_id == student_id) \
                .all()

    def get_full_schedule(self) -> List[Schedule]:
        with SessionLocal() as session:
            # Подвійний JOIN: склеюємо таблицю розкладу з аудиторіями, предметами ТА викладачами цих предметів
            return session.query(Schedule) \
                .options(
                joinedload(Schedule.discipline).joinedload(Discipline.teacher),
                joinedload(Schedule.classroom)
            ).all()

    def get_disciplines_with_details(self) -> List[Discipline]:
        with SessionLocal() as session:
            # Дістаємо дисципліни одразу разом із об'єктами викладачів
            return session.query(Discipline) \
                .options(joinedload(Discipline.teacher)) \
                .all()

    def upload_initial_data(self, data_dict: dict) -> None:
        """Пакетний імпорт та розумна синхронізація даних з Excel до SQLite."""
        with SessionLocal() as session:
            try:
                # 1. Завантажуємо викладачів (якщо такого ID ще немає в базі, то додаємо)
                for t in data_dict.get('teachers', []):
                    if not session.query(Teacher).filter(Teacher.id == t['id']).first():
                        session.add(Teacher(**t))

                # 2. Завантажуємо аудиторії
                for c in data_dict.get('classrooms', []):
                    if not session.query(Classroom).filter(Classroom.id == c['id']).first():
                        session.add(Classroom(**c))

                # 3. Завантажуємо студентів
                for s in data_dict.get('students', []):
                    if not session.query(Student).filter(Student.id == s['id']).first():
                        session.add(Student(**s))

                # Фіксуємо перші три таблиці в пам'яті бази, щоб з'явилися потрібні ID для зв'язків
                session.flush()

                # 4. Завантажуємо дисципліни
                for d in data_dict.get('disciplines', []):
                    if not session.query(Discipline).filter(Discipline.id == d['id']).first():
                        teacher_name = d.pop('teacher_name', None)
                        # Розумний зв'язок: шукаємо ID викладача в базі суто за його текстовим іменем з Excel
                        if teacher_name:
                            teacher = session.query(Teacher).filter(Teacher.name == teacher_name).first()
                            if teacher:
                                d['teacher_id'] = teacher.id
                        session.add(Discipline(**d))

                session.flush() # Ще раз оновлюємо стан, щоб зберегти нові предмети

                # 5. Завантажуємо журнал оцінок
                for g in data_dict.get('grades', []):
                    if not session.query(Grade).filter(Grade.id == g['id']).first():
                        student_name = g.pop('student_name', None)
                        discipline_title = g.pop('discipline_title', None)

                        # Автоматично переводимо текстове ім'я студента та назву предмету в цифрові Foreign Keys
                        if student_name:
                            st = session.query(Student).filter(Student.name == student_name).first()
                            if st: g['student_id'] = st.id
                        if discipline_title:
                            disc = session.query(Discipline).filter(Discipline.title == discipline_title).first()
                            if disc: g['discipline_id'] = disc.id

                        session.add(Grade(**g))

                # 6. Завантажуємо розклад занять
                for sch in data_dict.get('schedules', []):
                    if not session.query(Schedule).filter(Schedule.id == sch['id']).first():
                        discipline_title = sch.pop('discipline_title', None)
                        room_number = sch.pop('room_number', None)

                        if discipline_title:
                            disc = session.query(Discipline).filter(Discipline.title == discipline_title).first()
                            if disc: sch['discipline_id'] = disc.id

                        if room_number:
                            # Очищення тексту: прибираємо слово "Ауд. ", залишаючи чистий номер (наприклад, "403")
                            clean_room = str(room_number).replace("Ауд. ", "").replace("ауд. ", "").strip()
                            room = session.query(Classroom).filter(Classroom.room_number == clean_room).first()
                            if room:
                                sch['classroom_id'] = room.id

                        session.add(Schedule(**sch))

                # зберігаємо абсолютно весь імпортований пакет на жорсткий диск
                session.commit()
            except SQLAlchemyError as e:
                session.rollback() # Якщо помилка — скасовуємо всі зміни в сесії
                raise RuntimeError(f"Критична помилка під час пакетної синхронізації БД: {e}")


# Створюємо один єдиний глобальний об'єкт репозиторію для використання у всьому проекті
repository = UniversityRepository()