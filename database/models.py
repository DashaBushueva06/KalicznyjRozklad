# Вміст: Опис структури даних. Якщо використовується ORM, тут знаходяться класи таблиць (Student, Teacher, Course, Grade, Classroom, Schedule). Якщо використовується чистий SQL, тут можуть зберігатися DDL-запити (CREATE TABLE ...).
#
# Зв'язки: Не має внутрішніх залежностей від інших модулів проекту (лише імпорти бібліотек ORM).
#
# Експортується до: storage/db_repository.py.

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Student(Base):
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    group_id = Column(String(20), nullable=False)

    grades = relationship("Grade", back_populates="student", cascade="all, delete-orphan")


class Teacher(Base):
    __tablename__ = 'teachers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)

    courses = relationship("Course", back_populates="teacher")


class Course(Base):
    __tablename__ = 'courses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    teacher_id = Column(Integer, ForeignKey('teachers.id'), nullable=False)

    teacher = relationship("Teacher", back_populates="courses")
    grades = relationship("Grade", back_populates="course", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="course", cascade="all, delete-orphan")


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
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    value = Column(Integer, nullable=False)

    student = relationship("Student", back_populates="grades")
    course = relationship("Course", back_populates="grades")


class Schedule(Base):
    __tablename__ = 'schedules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    classroom_id = Column(Integer, ForeignKey('classrooms.id'), nullable=False)
    day_of_week = Column(String(20), nullable=False)
    time_slot = Column(String(20), nullable=False)

    course = relationship("Course", back_populates="schedules")
    classroom = relationship("Classroom", back_populates="schedules")