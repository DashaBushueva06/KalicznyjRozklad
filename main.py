# Вміст: Головна точка входу в додаток. Забезпечує первинне створення реляційних таблиць у SQLite,
# запускає початковий імпорт даних із файлу Excel та вмикає веб-сервер Flask на вказаному хості та порту.
#
# Зв'язки:
#   1. Імпортує низькорівневий двигун (engine) з database/connection.py для створення таблиць.
#   2. Імпортує базовий клас (Base) з database/models.py для зчитування структури моделей.
#   3. Імпортує готовий об'єкт веб-сервера (app) з server/app.py для його запуску.
#   4. Імпортує мережеві налаштування (SERVER_HOST, SERVER_PORT) з config/settings.py.
#   5. Імпортує модуль синхронізації (excel_handler) з storage/excel_handler.py.

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
    # 1. Автоматично створюємо фізичні таблиці в SQLite на основі наших Python-класів
    Base.metadata.create_all(bind=engine)

    # 2. Штучно відкриваємо контекст сервера, щоб безпечно завантажити перші дані з Excel
    with app.app_context():
        # Читаємо Excel-файл і повністю заповнюємо базу даних початковими студентами та розкладом
        excel_handler.import_all_data()


if __name__ == '__main__':
    # Спочатку готуємо базу даних та завантажуємо початкові дані
    initialize_system()

    # Вмикаємо Flask-сервер у мережу, передаючи йому IP-адресу (127.0.0.1) та порт (5000) з нашого конфігу
    app.run(host=SERVER_HOST, port=SERVER_PORT)