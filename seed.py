"""
Скрипт первинної ініціалізації бази даних (Data Seeding).
Заповнює таблиці тестовим набором даних та генерує валідний файл Excel.
"""

import os
from database.connection import engine
from database.models import Base
from storage.db_repository import repository
from storage.excel_handler import excel_handler
from config.settings import EXCEL_PATH


def seed_database():
    """Створення схеми БД та заповнення початковими даними."""

    # Видалення пошкодженого файлу Excel, якщо він існує
    if os.path.exists(EXCEL_PATH):
        os.remove(EXCEL_PATH)

    # Перестворення таблиць у базі даних SQLite
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # 1. Ініціалізація викладачів
    t1 = repository.teachers.create(name="Чайковський А.В.", department="Обчислювальної математики")
    t2 = repository.teachers.create(name="Бушуєва Д.О.", department="Прикладного програмування")

    # 2. Ініціалізація студентів
    s1 = repository.students.create(name="Сердюк С.", group_id="МТ-21")
    s2 = repository.students.create(name="Іванов І.", group_id="МТ-21")

    # 3. Ініціалізація курсів
    c1 = repository.courses.create(title="Прикладне програмування", teacher_id=t2.id)
    c2 = repository.courses.create(title="Математичний аналіз", teacher_id=t1.id)

    # 4. Ініціалізація аудиторій
    r1 = repository.classrooms.create(building="Головний", room_number="42", capacity=30)
    r2 = repository.classrooms.create(building="Головний", room_number="43", capacity=60)

    # 5. Ініціалізація оцінок
    repository.grades.create(student_id=s1.id, course_id=c1.id, value=95)
    repository.grades.create(student_id=s2.id, course_id=c2.id, value=88)

    # 6. Ініціалізація розкладу
    repository.schedules.create(
        day_of_week="Понеділок",
        time_slot="08:40 - 10:15",
        course_id=c1.id,
        classroom_id=r1.id
    )

    # Виклик методу синхронізації для створення валідного init_data.xlsx
    excel_handler.sync_all_data()
    print("Ініціалізація завершена: створено університетську БД та файл init_data.xlsx.")


if __name__ == "__main__":
    seed_database()