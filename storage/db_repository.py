"""
Модуль для виконання CRUD-операцій у реляційній базі даних.
Реалізує патерн Repository для інкапсуляції логіки роботи з SQLAlchemy.
"""

from typing import List, Optional, Type
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from database.connection import SessionLocal
from database.models import Base, Student, Teacher, Discipline, Classroom, Grade, Schedule


class BaseRepository:
    """Базовий клас репозиторію для стандартних CRUD-операцій."""

    def __init__(self, model: Type[Base]):
        self.model = model

    def get_all(self) -> List[Base]:
        with SessionLocal() as session:
            return session.query(self.model).all()

    def get_by_id(self, record_id: int) -> Optional[Base]:
        with SessionLocal() as session:
            return session.query(self.model).filter(self.model.id == record_id).first()

    def create(self, **kwargs) -> Base:
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
    """Спеціалізований репозиторій для конкретних сутностей предметної області."""

    def __init__(self):
        self.students = BaseRepository(Student)
        self.teachers = BaseRepository(Teacher)
        self.disciplines = BaseRepository(Discipline)
        self.classrooms = BaseRepository(Classroom)
        self.grades = BaseRepository(Grade)
        self.schedules = BaseRepository(Schedule)

    def get_grades_with_details(self) -> List[Grade]:
        with SessionLocal() as session:
            return session.query(Grade) \
                .options(joinedload(Grade.student), joinedload(Grade.discipline)) \
                .all()

    def get_student_grades(self, student_id: int) -> List[Grade]:
        with SessionLocal() as session:
            return session.query(Grade) \
                .options(joinedload(Grade.discipline)) \
                .filter(Grade.student_id == student_id) \
                .all()

    def get_full_schedule(self) -> List[Schedule]:
        with SessionLocal() as session:
            return session.query(Schedule) \
                .options(
                joinedload(Schedule.discipline).joinedload(Discipline.teacher),
                joinedload(Schedule.classroom)
            ).all()

    def get_disciplines_with_details(self) -> List[Discipline]:
        with SessionLocal() as session:
            return session.query(Discipline) \
                .options(joinedload(Discipline.teacher)) \
                .all()

    def upload_initial_data(self, data_dict: dict) -> None:
        """
        Пакетний імпорт та розумна синхронізація даних з Excel до SQLite.
        Пропускає вже існуючі ID, автоматично пов'язує текстові назви через Foreign Keys.
        """
        with SessionLocal() as session:
            try:
                # 1. Викладачі
                for t in data_dict.get('teachers', []):
                    if not session.query(Teacher).filter(Teacher.id == t['id']).first():
                        session.add(Teacher(**t))

                # 2. Аудиторії
                for c in data_dict.get('classrooms', []):
                    if not session.query(Classroom).filter(Classroom.id == c['id']).first():
                        session.add(Classroom(**c))

                # 3. Студенти
                for s in data_dict.get('students', []):
                    if not session.query(Student).filter(Student.id == s['id']).first():
                        session.add(Student(**s))

                session.flush()

                # 4. Дисципліни
                for d in data_dict.get('disciplines', []):
                    if not session.query(Discipline).filter(Discipline.id == d['id']).first():
                        teacher_name = d.pop('teacher_name', None)
                        if teacher_name:
                            teacher = session.query(Teacher).filter(Teacher.name == teacher_name).first()
                            if teacher:
                                d['teacher_id'] = teacher.id
                        session.add(Discipline(**d))

                session.flush()

                # 5. Оцінки
                for g in data_dict.get('grades', []):
                    if not session.query(Grade).filter(Grade.id == g['id']).first():
                        student_name = g.pop('student_name', None)
                        discipline_title = g.pop('discipline_title', None)

                        if student_name:
                            st = session.query(Student).filter(Student.name == student_name).first()
                            if st: g['student_id'] = st.id
                        if discipline_title:
                            disc = session.query(Discipline).filter(Discipline.title == discipline_title).first()
                            if disc: g['discipline_id'] = disc.id

                        session.add(Grade(**g))

                # 6. Розклад
                for sch in data_dict.get('schedules', []):
                    if not session.query(Schedule).filter(Schedule.id == sch['id']).first():
                        discipline_title = sch.pop('discipline_title', None)
                        room_number = sch.pop('room_number', None)

                        if discipline_title:
                            disc = session.query(Discipline).filter(Discipline.title == discipline_title).first()
                            if disc: sch['discipline_id'] = disc.id

                        if room_number:
                            # Відсікаємо префікси, якщо вони є в Excel (наприклад, "Ауд. 403" -> "403")
                            clean_room = str(room_number).replace("Ауд. ", "").replace("ауд. ", "").strip()
                            room = session.query(Classroom).filter(Classroom.room_number == clean_room).first()
                            if room:
                                sch['classroom_id'] = room.id

                        session.add(Schedule(**sch))

                session.commit()
            except SQLAlchemyError as e:
                session.rollback()
                raise RuntimeError(f"Критична помилка під час пакетної синхронізації БД: {e}")


repository = UniversityRepository()