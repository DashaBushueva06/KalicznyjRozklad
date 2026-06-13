# Вміст: Створення двигуна підключення (Engine) до СУБД SQLite та налаштування конвеєра (фабрики) для генерації індивідуальних сесій взаємодії з базою даних через ORM SQLAlchemy.
#
# Зв'язки: Імпортує рядок підключення (DATABASE_URL) з конфігураційного файла config/settings.py.
#
# Експортується до:
#   1. storage/db_repository.py — для створення сесій Unit of Work (SessionLocal) при виконанні CRUD-операцій.
#   2. main.py — для зв'язування метаданих і первинного створення таблиць у базі даних (Base.metadata.create_all).

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import DATABASE_URL

# Ініціалізація низькорівневого підключення до БД (echo=False вимикає виведення сирих SQL-запитів у консоль)
engine = create_engine(DATABASE_URL, echo=False)

# Налаштування фабрики сесій; вимикаємо авто-збереження для ручного контролю
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session():
    """
    Генератор для отримання об'єкта сесії БД.
    Гарантує коректне закриття з'єднання після виконання операцій.
    """
    # Створюємо нову чисту сесію для роботи з даними
    db = SessionLocal()
    try:
        # Повертаємо сесію для виконання операцій
        return db
    finally:
        # Цей блок виконається в будь-якому випадку, примусово закриваючи сесію та звільняючи пам'ять
        db.close()