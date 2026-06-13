import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server.app import app
from database.models import Base
import storage.db_repository


# 'sqlite:///:memory:' - база даних не зберігається у файл, створюється прямо в RAM, і після завершення зникає
test_engine = create_engine('sqlite:///:memory:', echo=False)

# Створюю спеціальну тестову сесію - окреме з'єднання з віртуальною БД в пам'яті
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Замінюю SessionLocal на тестову TestingSessionLocal.
# Бекенд буде писати й читати дані не з жорсткого диска, а з RAM
storage.db_repository.SessionLocal = TestingSessionLocal


class TestUniversityManagementSystem(unittest.TestCase):
    def setUp(self): # Ініціалізація перед кожним окремим тестом
        self.app = app.test_client() # test_client - віртуальний браузер
        self.app.testing = True  # Вмикаю режим тестування у Flask, щоб бачити розгорнуті помилки
        Base.metadata.create_all(bind=test_engine) # Створюю всі таблиці (Студенти, Викладачі тощо) у нашій порожній базі в пам'яті

    def tearDown(self): # Очищення ресурсів після кожного окремого тесту
        Base.metadata.drop_all(bind=test_engine)

    # Перший тест: Перевірка доступності головної сторінки (тестую маршрут '/')
    def test_index_route(self):
        response = self.app.get('/') # Віртуальний браузер робить запит на головну сторінку
        self.assertEqual(response.status_code, 200) # Перевіряю, чи сервер відповів "200 OK" (сторінка успішно завантажилась)


    # Другий тест: Перевірка доступу до сторінки студентів (тестую маршрут '/students')
    def test_students_get_route(self):
        response = self.app.get('/students')
        self.assertEqual(response.status_code, 200)

    # Третій тест: Перевірка додавання студентів через POST-запит форми
    def test_add_student(self):
        response = self.app.post( # Імітую натискання кнопки "Зберегти" у HTML-формі
            '/students/add',
            data={'name': 'Тестовий Студент', 'specialization': 'Статистика', 'course': '2'},
            follow_redirects=True   # follow_redirects=True каже тестовому клієнту автоматично перейти на сторінку списку
                                    # після перенаправлення, повністю імітуючи поведінку браузера
        )
        self.assertEqual(response.status_code, 200) # Перевіряю, чи сторінка не впала (код 200)

        students = storage.db_repository.repository.students.get_all() # Перевіряю чи запис зберігся
        self.assertEqual(len(students), 1) # Стверджую, що в базі має бути рівно 1 студент
        self.assertEqual(students[0].name, 'Тестовий Студент') # Стверджуємо, що ім'я цього студента збігається з тим, що відправляла

    # Четвертий тест: Перевірка циклу створення та видалення студента в базі
    def test_add_and_delete_student(self):
        # Прямо через код створюємо студента в тестовій БД з правильними полями
        storage.db_repository.repository.students.create(name='Студент Видалення', specialization='Математика',
                                                         course='2')
        students_before = storage.db_repository.repository.students.get_all()
        student_id = students_before[0].id  # Запам'ятовую його ID

        # Імітую клац по кнопці "Видалити"
        response = self.app.post(f'/students/{student_id}/delete', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Перевіряю чи студент зник
        students_after = storage.db_repository.repository.students.get_all()
        self.assertEqual(len(students_after), 0)  # Довжина списку має бути 0


    # П'ятий тест: Перевірка створення дисципліни із зовнішнім ключем викладача
    def test_add_discipline_with_foreign_key(self):
        # Спочатку створюю викладача, бо без нього дисципліна не зможе існувати
        teacher = storage.db_repository.repository.teachers.create(name='Тестовий Викладач', department='Кафедра ІТ')
        response = self.app.post( # Відправляємо форму створення дисципліни, прив'язуючи її до ID щойно створеного викладача
            '/disciplines/add',
            data={'title': 'Прикладне програмування', 'teacher_id': teacher.id},
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        disciplines = storage.db_repository.repository.disciplines.get_all() # Перевіряю, чи зберігся зв'язок у базі даних
        self.assertEqual(len(disciplines), 1)
        self.assertEqual(disciplines[0].teacher_id, teacher.id) # Стверджую, що ID викладача у дисципліні відповідає ID тестового викладача


if __name__ == '__main__':
    unittest.main()