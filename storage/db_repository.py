from typing import List, Optional, Type
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from database.connection import SessionLocal
from database.models import Base, Student, Teacher, Discipline, Classroom, Grade, Schedule


class BaseRepository:
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
    def __init__(self):
        self.students = BaseRepository(Student)
        self.teachers = BaseRepository(Teacher)
        self.disciplines = BaseRepository(Discipline) # Перейменовано
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


repository = UniversityRepository()