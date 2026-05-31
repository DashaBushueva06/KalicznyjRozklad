# Вміст: Ініціалізація екземпляра веб-сервера (Flask app = Flask(__name__) або FastAPI app = FastAPI()). Налаштування middleware та підключення маршрутизаторів.
#
# Зв'язки: Імпортує server/routes.py для реєстрації маршрутів. Імпортує config/settings.py для налаштувань запуску (порт, хост).
#
# Експортується до: main.py (для запуску сервера).

"""
Модуль ініціалізації веб-сервера Flask.
Відповідає за налаштування екземпляра додатка та реєстрацію контексту.
"""

from flask import Flask
from config.settings import DEBUG_MODE


def create_app() -> Flask:
    """
    Ініціалізація та конфігурація Flask-додатка.
    Маршрути імпортуються всередині контексту додатка.
    """
    # Вказуємо Flask шукати шаблони в директорії server/templates
    app = Flask(__name__, template_folder='templates')

    # Секретний ключ необхідний для безпечної роботи сесій (Flash-повідомлень)
    app.config['SECRET_KEY'] = 'university_management_secure_key_123'
    app.config['DEBUG'] = DEBUG_MODE

    with app.app_context():
        # Реєстрація HTTP-ендпоінтів
        import server.routes

    return app


# Глобальний екземпляр сервера для запуску через main.py
app = create_app()