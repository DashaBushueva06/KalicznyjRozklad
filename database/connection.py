# Вміст: Логіка підключення до бази даних (SQLite). Містить функцію або клас для створення сесії (якщо використовується ORM, наприклад SQLAlchemy) або об'єкта cursor (для сирого sqlite3).
#
# Зв'язки: Імпортує шляхи з config/settings.py.
#
# Експортується до: storage/db_repository.py, main.py (для первинної ініціалізації таблиць).
#

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import DATABASE_URL

# Ініціалізація підключення до БД (echo=False вимикає логування кожного SQL-запиту в консоль)
engine = create_engine(DATABASE_URL, echo=False)

# Фабрика сесій
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session():
    """
    Генератор для отримання об'єкта сесії БД.
    Гарантує коректне закриття з'єднання після виконання операцій.
    """
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()