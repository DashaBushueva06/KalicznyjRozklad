"""
Структура даних. Визначає моделі SQLAlchemy для таблиць бази даних.
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Student(Base):
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    specialization = Column(String(100), nullable=False)  # "Математика", "Статистика", etc.
    course = Column(String(50), nullable=False)  # "1 курс бакалаврату", "1 курс магістратури", etc.

    grades = relationship("Grade", back_populates="student", cascade="all, delete-orphan")


class Teacher(Base):
    __tablename__ = 'teachers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)

    disciplines = relationship("Discipline", back_populates="teacher")


class Discipline(Base):
    __tablename__ = 'disciplines'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    teacher_id = Column(Integer, ForeignKey('teachers.id'), nullable=False)

    teacher = relationship("Teacher", back_populates="disciplines")
    grades = relationship("Grade", back_populates="discipline", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="discipline", cascade="all, delete-orphan")


class Classroom(Base):
    __tablename__ = 'classrooms'

    id = Column(Integer, primary_key=True, autoincrement=True)
    building = Column(String(50), nullable=False)
    room_number = Column(String(20), nullable=False)
    capacity = Column(Integer, nullable=False)

    schedules = relationship("Schedule", back_populates="classroom")


class Grade(Base):
    __tablename__ = 'grades'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    discipline_id = Column(Integer, ForeignKey('disciplines.id'), nullable=False)
    value = Column(Integer, nullable=False)

    student = relationship("Student", back_populates="grades")
    discipline = relationship("Discipline", back_populates="grades")


class Schedule(Base):
    __tablename__ = 'schedules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    discipline_id = Column(Integer, ForeignKey('disciplines.id'), nullable=False)
    classroom_id = Column(Integer, ForeignKey('classrooms.id'), nullable=False)
    day_of_week = Column(String(20), nullable=False)
    time_slot = Column(String(20), nullable=False)

    discipline = relationship("Discipline", back_populates="schedules")
    classroom = relationship("Classroom", back_populates="schedules")
