# Вміст: Глобальні константи, налаштування середовища (ENV) та шляхи до файлів. Використовує модуль pathlib для формування абсолютних шляхів до бази даних та Excel-файлу, незалежно від операційної системи.

#Зв'язки: Не імпортує інші модулі проекту.

#Експортується до: database/connection.py, storage/excel_handler.py, server/app.py для отримання конфігураційних параметрів.


import os
from pathlib import Path

# Базова директорія проекту (на два рівні вище за цей файл)
BASE_DIR = Path(__file__).resolve().parent.parent

# Шляхи до каталогу даних та конкретних файлів
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "university.db"
EXCEL_PATH = DATA_DIR / "init_data.xlsx"

# Рядок підключення для SQLAlchemy
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Системні параметри сервера
SERVER_HOST = os.environ.get("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.environ.get("SERVER_PORT", 5000))
DEBUG_MODE = True