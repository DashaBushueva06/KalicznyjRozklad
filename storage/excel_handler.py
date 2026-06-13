import os
import zipfile

from openpyxl import load_workbook, Workbook # load_workbook-читання дійсних файлів, Workbook-для створення нових
from openpyxl.styles import PatternFill, Font # PatternFill та Font потрібні для заливки фону клітинок, зміни кольору тексту
from openpyxl.utils import get_column_letter # get_column_letter потрібен, щоб перетворювати числові індекси колонок (1, 2, 3) у літери Excel (A, B, C)
from config.settings import EXCEL_PATH


class ExcelHandler:
    def __init__(self, file_path: str):
        self.file_path = file_path

    # _get_workbook: Відкриває дійсну книгу Excel або створює нову, якщо файл пошкоджено
    def _get_workbook(self) -> Workbook:
        if not os.path.exists(self.file_path) or os.path.getsize(self.file_path) == 0:
            wb = Workbook() # Створюю чисту книгу
            wb.save(self.file_path) # Зберігаю на диск
            return wb

        try:
            return load_workbook(self.file_path)
        except zipfile.BadZipFile:
            wb = Workbook()
            wb.save(self.file_path)
            return wb


    # _export_sheet: Створює аркуш, стилізує шапку та автоматично підбирає ширину колонок
    @staticmethod # економить оперативну пам'ять
    def _export_sheet(wb: Workbook, sheet_name: str, headers: list, data: list) -> None:
        if sheet_name in wb.sheetnames:
            std = wb[sheet_name]
            wb.remove(std)  # Очищення старого аркуша, якщо він вже існує

        ws = wb.create_sheet(sheet_name)
        ws.append(headers) # Записую перший рядок із заголовками

        for row in data:
            ws.append(row) # Проходжуся по масиву даних і дописую їх рядок за рядком

        # Фарбую шапку, вказую темно-синій колір
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True) #  Текст шапки білий та жирний

        for cell in ws[1]: # Проходжусь циклом по всіх клітинках першого рядка (ws[1] - шапка)
            cell.fill = header_fill # Заливаю синім
            cell.font = header_font # Застосовую білий жирний шрифт

        # Розумний автопідбір ширини колонок під контент
        for col in ws.columns: # Перебираю всі колонки на аркуші (A, B, C і так далі)
            max_length = 0 # Змінна для збереження максимальної довжини тексту в колонці
            column_letter = get_column_letter(col[0].column) # Витягую літеру поточної колонки

            for cell in col: # Перебираю всі клітинки всередині поточної колонки (зверху вниз)
                if cell.value: # Якщо клітинка не порожня
                    cell_length = len(str(cell.value)) # Рахую довжину тексту в клітинці
                    if cell_length > max_length: # Якщо знайдений текст довший за попередній максимум - оновлюю рекорд
                        max_length = cell_length

            # Встановлюю вирахувану ширину для всієї колонки
            ws.column_dimensions[column_letter].width = max_length + 2


    # import_all_data: Зчитує дані з аркушів та імпортує їх у базу даних SQLite
    def import_all_data(self) -> None:
        from storage.db_repository import repository # Локальний імпорт для захисту від кільцевого імпорту

        if not os.path.exists(self.file_path):
            print(f"[ERROR] Initialization file {self.file_path} not found.")
            return
        print(f"[INFO] Synchronizing current data from Excel file: {self.file_path}")

        wb = load_workbook(self.file_path, data_only=True)  # Зчитую файл. data_only=True каже брати самі значення, а не формули

        data_to_import = {  # Словник-контейнер для пакетного відправлення в БД
            'teachers': [], 'classrooms': [], 'students': [],
            'disciplines': [], 'grades': [], 'schedules': []
        }

        mapping = { # Мапа зв'язків, де ключ - назва аркуша, а значення - кортеж
            "Викладачі": ('teachers', ['id', 'name', 'department']),
            "Аудиторії": ('classrooms', ['id', 'room_number', 'capacity']),
            "Студенти": ('students', ['id', 'name', 'specialization', 'course']),
            "Дисципліни": ('disciplines', ['id', 'title', 'teacher_name']),
            "Оцінки": ('grades', ['id', 'student_name', 'discipline_title', 'value'])
        }

        for sheet_name, (db_key, fields) in mapping.items(): # 1 цикл для 5 стандартних аркушів
            if sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                for row in ws.iter_rows(min_row=2, values_only=True):  # Іду по всіх рядках, пропускаючи шапку
                    if row and row[0] is not None:  # Захист від порожніх рядків
                        # Функція zip об'єднує назви полів [id, name...] з даними рядка у готовий словник
                        data_to_import[db_key].append(dict(zip(fields, row)))

        # 2. Окремо аркуш Розклад, бо у нього складна логіка з дефолтними значеннями
        if "Розклад" in wb.sheetnames:
            ws = wb["Розклад"]
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row and row[0] is not None:
                    data_to_import['schedules'].append({  # Пакую складний об'єкт розкладу з перевірками довжини
                        'id': int(row[0]), 'day_of_week': str(row[1]), 'time_slot': str(row[2]),
                        'discipline_title': str(row[3]), 'room_number': str(row[4]),
                        'specialization': str(row[5]) if len(row) > 5 and row[5] else "Загальна",
                        'course': str(row[6]) if len(row) > 6 and row[6] else "1"
                    })

        try:
            repository.upload_initial_data(data_to_import) # Завантажую всі зібрані дані в базу даних
            print("[SUCCESS] Excel -> DB synchronization completed successfully.")
        except Exception as e:
            print(f"[CRITICAL] Batch save error occurred: {e}")


    # sync_all_data: Вивантажує поточний стан усіх таблиць бази даних назад у файл Excel
    def sync_all_data(self) -> None:
        from storage.db_repository import repository
        wb = self._get_workbook()

        export_mapping = [
            ("Студенти", ["ID", "ПІБ", "Спеціальність", "Курс"],
             repository.students.get_all(), lambda s: [s.id, s.name, s.specialization, s.course]),
            ("Викладачі", ["ID", "ПІБ", "Кафедра"],
             repository.teachers.get_all(), lambda t: [t.id, t.name, t.department]),
            ("Дисципліни", ["ID", "Назва дисципліни", "Викладач"],
             repository.get_disciplines_with_details(),
             lambda d: [d.id, d.title, d.teacher.name if d.teacher else "Невідомо"]),
            ("Аудиторії", ["ID", "Номер аудиторії", "Місткість"],
             repository.classrooms.get_all(), lambda r: [r.id, r.room_number, r.capacity])
        ]

        for sheet_name, headers, fetch_method, transform_func in export_mapping: # 1 цикл для експорту базових таблиць
            # Викликаю метод експорту без self
            self._export_sheet(wb, sheet_name, headers, [transform_func(obj) for obj in fetch_method])

        # Окремо аркуш Оцінки, бо там довга логіка трансформації рядка
        grades = repository.get_grades_with_details()  # Завантажую оцінки з бази
        self._export_sheet(wb, "Оцінки", ["ID", "Студент", "Дисципліна", "Оцінка"],
                           [[g.id, g.student.name if g.student else "Невідомо",
                             g.discipline.title if g.discipline else "Невідомо", g.value] for g in grades])

        # Окремо аркуш Розклад, через кастомне форматування назви аудиторії
        schedules = repository.get_full_schedule()
        self._export_sheet(wb, "Розклад",
                           ["ID", "День тижня", "Час", "Дисципліна", "Аудиторія", "Спеціальність", "Курс"],
                           [[s.id, s.day_of_week, s.time_slot,
                             s.discipline.title if s.discipline else "Невідомо",
                             f"Ауд. {s.classroom.room_number}" if s.classroom else "Невідомо",
                             s.specialization, s.course]
                            for s in schedules])

        if "Sheet" in wb.sheetnames and len(wb.sheetnames) > 1:
            wb.remove(wb["Sheet"]) # Прибираю стандартний порожній аркуш Excel

        wb.save(self.file_path)

excel_handler = ExcelHandler(EXCEL_PATH)