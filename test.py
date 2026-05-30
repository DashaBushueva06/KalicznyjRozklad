import unittest
import os
from server import LMSDatabase


class TestLMSSystem(unittest.TestCase):
    def setUp(self):
        # Використовуємо окрему тестову базу, щоб не псувати основну
        self.test_db = "test_lms.db"
        self.db = LMSDatabase(self.test_db)

    def tearDown(self):
        # Закриваємо з'єднання та видаляємо тестову базу після кожного тесту
        self.db.conn.close()
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_add_and_get_student(self):
        """Перевіряє, чи працює додавання та читання студентів."""
        # 1. Додаємо студента (використовуємо новий універсальний метод execute_query)
        _, student_id = self.db.execute_query(
            "INSERT INTO students (name, major) VALUES (?, ?)",
            ("Дарія", "Статистика")
        )

        # 2. Читаємо студентів з бази
        students, _ = self.db.execute_query("SELECT * FROM students")

        # 3. Перевіряємо (assert), чи все збігається
        self.assertEqual(len(students), 1)
        self.assertEqual(students[0][1], "Дарія")
        self.assertEqual(students[0][2], "Статистика")
        self.assertEqual(student_id, 1)


if __name__ == '__main__':
    unittest.main()