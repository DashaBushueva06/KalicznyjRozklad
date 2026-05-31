# Вміст: Набір функцій або клас із методами для виконання CRUD-операцій у реляційній базі даних (наприклад, get_all_students(), add_student(), delete_course()).
#
# Зв'язки: Імпортує database/connection.py та database/models.py.
#
# Експортується до: server/routes.py (маршрутизатори викликають ці функції для модифікації БД).

"""
Модуль для виконання CRUD-операцій у реляційній базі даних.
Реалізує патерн Repository для інкапсуляції логіки роботи з SQLAlchemy.
"""

from typing import List, Optional, Type, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from database.connection import SessionLocal
from database.models import Base, Student, Teacher, Course, Classroom, Grade, Schedule


class BaseRepository:
    """
    Базовий клас репозиторію.
    Містить узагальнені методи для стандартних CRUD-операцій,
    які підходять для будь-якої моделі SQLAlchemy.
    """

    def __init__(self, model: Type[Base]):
        self.model = model

    def get_all(self) -> List[Base]:
        """Отримання всіх записів таблиці."""
        with SessionLocal() as session:
            return session.query(self.model).all()

    def get_by_id(self, record_id: int) -> Optional[Base]:
        """Отримання запису за первинним ключем."""
        with SessionLocal() as session:
            return session.query(self.model).filter(self.model.id == record_id).first()

    def create(self, **kwargs) -> Base:
        """Створення нового запису."""
        with SessionLocal() as session:
            try:
                new_record = self.model(**kwargs)
                session.add(new_record)
                session.commit()
                session.refresh(new_record)
                return new_record
            except SQLAlchemyError as e:
                session.rollback()
                raise RuntimeError(f"Помилка створення запису в {self.model.__tablename__}: {e}")

    def update(self, record_id: int, **kwargs) -> Optional[Base]:
        """Оновлення існуючого запису."""
        with SessionLocal() as session:
            try:
                record = session.query(self.model).filter(self.model.id == record_id).first()
                if not record:
                    return None

                for key, value in kwargs.items():
                    if hasattr(record, key):
                        setattr(record, key, value)

                session.commit()
                session.refresh(record)
                return record
            except SQLAlchemyError as e:
                session.rollback()
                raise RuntimeError(f"Помилка оновлення запису в {self.model.__tablename__}: {e}")

    def delete(self, record_id: int) -> bool:
        """Видалення запису за ідентифікатором."""
        with SessionLocal() as session:
            try:
                record = session.query(self.model).filter(self.model.id == record_id).first()
                if not record:
                    return False
                session.delete(record)
                session.commit()
                return True
            except SQLAlchemyError as e:
                session.rollback()
                raise RuntimeError(f"Помилка видалення запису з {self.model.__tablename__}: {e}")


class UniversityRepository:
    """
    Спеціалізований репозиторій для конкретних сутностей предметної області.
    Містить екземпляри базових репозиторіїв та методи для складних JOIN-запитів.
    """

    def __init__(self):
        self.students = BaseRepository(Student)
        self.teachers = BaseRepository(Teacher)
        self.courses = BaseRepository(Course)
        self.classrooms = BaseRepository(Classroom)
        self.grades = BaseRepository(Grade)
        self.schedules = BaseRepository(Schedule)

    # --- Спеціалізовані методи для складних вибірок (JOIN) ---

    def get_grades_with_details(self) -> List[Grade]:
        """
        Отримання всіх оцінок із підтягуванням пов'язаних об'єктів
        (Студент та Курс) за допомогою joinedload.
        Мінімізує проблему N+1 запитів.
        """
        with SessionLocal() as session:
            return session.query(Grade) \
                .options(joinedload(Grade.student), joinedload(Grade.course)) \
                .all()

    def get_student_grades(self, student_id: int) -> List[Grade]:
        """Отримання успішності конкретного студента."""
        with SessionLocal() as session:
            return session.query(Grade) \
                .options(joinedload(Grade.course)) \
                .filter(Grade.student_id == student_id) \
                .all()

    def get_full_schedule(self) -> List[Schedule]:
        """
        Отримання розкладу із завантаженням деталей про курс,
        викладача та аудиторію.
        """
        with SessionLocal() as session:
            return session.query(Schedule) \
                .options(
                joinedload(Schedule.course).joinedload(Course.teacher),
                joinedload(Schedule.classroom)
            ).all()

    def get_courses_with_details(self) -> List[Course]:
        """Отримання списку курсів із попереднім завантаженням пов'язаних викладачів."""
        with SessionLocal() as session:
            return session.query(Course) \
                .options(joinedload(Course.teacher)) \
                .all()

# Додайте цей метод всередину класу UniversityRepository
    def get_courses_with_details(self) -> List[Course]:
        """
        Отримання списку курсів із попереднім завантаженням пов'язаних викладачів.
        Запобігає DetachedInstanceError під час рендерингу шаблонів.
        """
        with SessionLocal() as session:
            return session.query(Course)\
                .options(joinedload(Course.teacher))\
                .all()


# Глобальний екземпляр репозиторію для використання у маршрутизаторах (routes.py)
repository = UniversityRepository()