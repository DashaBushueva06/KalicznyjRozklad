# Вміст: Головний файл (точка входу).
#
# Алгоритм виконання: Перевіряє наявність БД. Якщо порожня — викликає функцію парсингу з excel_handler.py та записує дані через db_repository.py. Після ініціалізації даних запускає веб-сервер із server/app.py (виклик app.run()).
#
# Зв'язки: Імпортує server/app.py, storage/excel_handler.py, storage/db_repository.py.

"""
Головний виконуваний файл системи управління навчальним процесом.
Ініціалізує структуру бази даних та запускає веб-сервер.
"""

from database.connection import engine
from database.models import Base
from server.app import app
from config.settings import SERVER_HOST, SERVER_PORT

def initialize_system() -> None:
    """
    Створення таблиць у базі даних (SQLite) відповідно до моделей SQLAlchemy.
    Метод create_all безпечний: він не перезаписує існуючі таблиці.
    """
    Base.metadata.create_all(bind=engine)

if __name__ == '__main__':
    initialize_system()
    # Запуск Flask-сервера
    app.run(host=SERVER_HOST, port=SERVER_PORT)