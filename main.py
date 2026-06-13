"""
Головний виконуваний файл системи управління навчальним процесом.
Ініціалізує структуру бази даних, синхронізує стартові дані з Excel
та запускає веб-сервер.
"""

from database.connection import engine
from database.models import Base
from server.app import app
from config.settings import SERVER_HOST, SERVER_PORT
from storage.excel_handler import excel_handler


def initialize_system() -> None:
    """
    Створення таблиць у базі даних (SQLite) відповідно до моделей SQLAlchemy.
    Метод create_all безпечний: він не перезаписує існуючі таблиці.
    """
    # 1. Ініціалізація структури таблиць у SQLite
    Base.metadata.create_all(bind=engine)

    # 2. Розумне довантаження та синхронізація даних із Excel у базу даних
    with app.app_context():
        excel_handler.import_all_data()


if __name__ == '__main__':
    initialize_system()

    # Запуск Flask-сервера
    app.run(host=SERVER_HOST, port=SERVER_PORT)