"""
Модуль модульного тестування (Unit Tests).
Використовує ізольовану In-Memory SQLite базу даних для уникнення конфліктів з основними даними.
"""

import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server.app import app
from database.models import Base
import storage.db_repository

# Ініціалізація тестового рушія бази даних в оперативній пам'яті
test_engine = create_engine('sqlite:///:memory:', echo=False)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Перевизначення фабрики сесій у модулі репозиторію
storage.db_repository.SessionLocal = TestingSessionLocal


class TestUniversityManagementSystem(unittest.TestCase):

    def setUp(self):
        """Ініціалізація перед кожним тестом."""
        self.app = app.test_client()
        self.app.testing = True

        # Створення структури таблиць у тестовій БД
        Base.metadata.create_all(bind=test_engine)

    def tearDown(self):
        """Очищення ресурсів після кожного тесту."""
        Base.metadata.drop_all(bind=test_engine)

    # ==========================================
    # Тестування доступності GET-маршрутів
    # ==========================================

    def test_index_route(self):
        """Перевірка доступності головної сторінки."""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    def test_students_get_route(self):
        """Перевірка доступу до списку студентів."""
        response = self.app.get('/students')
        self.assertEqual(response.status_code, 200)

    # ==========================================
    # Тестування POST-операцій (Створення та Видалення)
    # ==========================================

    def test_add_student(self):
        """Перевірка додавання студентів."""
        response = self.app.post(
            '/students/add',
            data={'name': 'Тестовий Студент', 'group_id': 'КН-11'},
            follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)

        students = storage.db_repository.repository.students.get_all()
        self.assertEqual(len(students), 1)
        self.assertEqual(students[0].name, 'Тестовий Студент')

    def test_add_and_delete_student(self):
        """Перевірка циклу створення та видалення студента."""
        storage.db_repository.repository.students.create(name='Студент Видалення', group_id='КН-22')
        students_before = storage.db_repository.repository.students.get_all()
        student_id = students_before[0].id

        response = self.app.post(f'/students/{student_id}/delete', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        students_after = storage.db_repository.repository.students.get_all()
        self.assertEqual(len(students_after), 0)

    def test_add_course_with_foreign_key(self):
        """Перевірка додавання сутності із зовнішнім ключем."""
        teacher = storage.db_repository.repository.teachers.create(name='Тестовий Викладач', department='Кафедра ІТ')

        response = self.app.post(
            '/courses/add',
            data={'title': 'Прикладне програмування', 'teacher_id': teacher.id},
            follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)

        courses = storage.db_repository.repository.courses.get_all()
        self.assertEqual(len(courses), 1)
        self.assertEqual(courses[0].teacher_id, teacher.id)


if __name__ == '__main__':
    unittest.main()