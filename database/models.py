# Вміст: опис структури реляційних таблиць СУБД за допомогою ORM SQLAlchemy, визначення типів полів, первинних та зовнішніх ключів (Foreign Keys), а також налаштування каскадних зв'язків між сутностями.
#
# Зв'язки: Не імпортує інші модулі проекту.
#
# Експортується до:
#   1. database/connection.py та main.py — для зчитування метаданих об'єкта Base та автоматичного створення фізичних таблиць у SQLite.
#   2. storage/db_repository.py — для виконання CRUD-операцій безпосередньо над класами-моделями (Student, Teacher тощо).

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

# Створюємо базовий клас, від якого будуть успадковуватися всі наші таблиці-моделі
Base = declarative_base()

# --- Таблиця Студентів ---
class Student(Base):
    __tablename__ = 'students' # Ім'я таблиці у фізичній базі даних SQLite

    id = Column(Integer, primary_key=True, autoincrement=True) # Унікальний ID студента
    name = Column(String(100), nullable=False)                 # ПІБ (макс. 100 символів, не може бути порожнім)
    specialization = Column(String(100), nullable=False)       # Спеціальність (наприклад, "Статистика")
    course = Column(String(50), nullable=False)                # Курс навчання

    # Віртуальний зв'язок: автоматично підтягує всі оцінки студента; при видаленні студента — видаляє і його оцінки
    grades = relationship("Grade", back_populates="student", cascade="all, delete-orphan")


# --- Таблиця Викладачів ---
class Teacher(Base):
    __tablename__ = 'teachers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)           # Кафедра викладача

    # Віртуальний зв'язок: якщо видалити викладача — автоматично видаляться і предмети, які він вів
    disciplines = relationship("Discipline", back_populates="teacher", cascade="all, delete-orphan")


# --- Таблиця Дисципліні (Предметів) ---
class Discipline(Base):
    __tablename__ = 'disciplines'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)                # Назва предмету
    # Зовнішній ключ: зв'язок "багато предметів до одного викладача" через його ID
    teacher_id = Column(Integer, ForeignKey('teachers.id'), nullable=False)

    # Налаштування двостороннього зв'язку з моделлю Викладача
    teacher = relationship("Teacher", back_populates="disciplines")
    # При видаленні предмету — автоматично видаляються всі виставлені за нього оцінки та його записи в розкладі
    grades = relationship("Grade", back_populates="discipline", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="discipline", cascade="all, delete-orphan")


# --- Таблиця Аудиторій ---
class Classroom(Base):
    __tablename__ = 'classrooms'

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_number = Column(String(20), nullable=False)           # Номер аудиторії
    capacity = Column(Integer, nullable=False)                 # Місткість

    # Зв'язок із таблицею розкладу (без каскадного видалення, щоб при знесенні кабінету пари не зникали самі)
    schedules = relationship("Schedule", back_populates="classroom")


# --- Таблиця Оцінок ---
class Grade(Base):
    __tablename__ = 'grades'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Зовнішні ключі, які пов'язують оцінку з конкретним студентом та конкретним предметом
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    discipline_id = Column(Integer, ForeignKey('disciplines.id'), nullable=False)
    value = Column(Integer, nullable=False)                    # Числове значення оцінки (бал)

    # Двосторонні посилання для швидкого доступу до об'єктів Студента та Предмету прямо з оцінки
    student = relationship("Student", back_populates="grades")
    discipline = relationship("Discipline", back_populates="grades")


# --- Таблиця Розкладу Занять ---
class Schedule(Base):
    __tablename__ = 'schedules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Посилання на предмет та кабінет, де проходитиме пара
    discipline_id = Column(Integer, ForeignKey('disciplines.id'), nullable=False)
    classroom_id = Column(Integer, ForeignKey('classrooms.id'), nullable=False)
    day_of_week = Column(String(20), nullable=False)
    time_slot = Column(String(20), nullable=False)
    specialization = Column(String(100), nullable=False)
    course = Column(String(50), nullable=False)

    # Двосторонні посилання для збору повної картини розкладу через JOIN-запити
    discipline = relationship("Discipline", back_populates="schedules")
    classroom = relationship("Classroom", back_populates="schedules")
