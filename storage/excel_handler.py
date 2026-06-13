"""
Модуль для роботи з документами Excel за допомогою openpyxl.
Забезпечує двосторонню синхронізацію: експорт стану бази у файл init_data.xlsx
та розумний імпорт оновлень назад у базу SQLite.
"""

import os
import zipfile
from openpyxl import load_workbook, Workbook
from config.settings import EXCEL_PATH


class ExcelHandler:
    """Клас для інкапсуляції логіки взаємодії з файловою системою та Excel."""

    def __init__(self, file_path: str):
        self.file_path = file_path

    def _get_workbook(self) -> Workbook:
        """Отримання об'єкта робочої книги. Створення нової у разі пошкодження або відсутності."""
        if not os.path.exists(self.file_path) or os.path.getsize(self.file_path) == 0:
            wb = Workbook()
            wb.save(self.file_path)
            return wb

        try:
            return load_workbook(self.file_path)
        except zipfile.BadZipFile:
            wb = Workbook()
            wb.save(self.file_path)
            return wb

    def _export_sheet(self, wb: Workbook, sheet_name: str, headers: list, data: list) -> None:
        """Формування окремого аркуша з попереднім видаленням старої версії."""
        if sheet_name in wb.sheetnames:
            std = wb[sheet_name]
            wb.remove(std)

        ws = wb.create_sheet(sheet_name)
        ws.append(headers)

        for row in data:
            ws.append(row)

    def import_all_data(self) -> None:
        """Зчитування даних з Excel та їх розумне довантаження у базу даних SQLite."""
        from storage.db_repository import repository  # Локальний імпорт проти циклічності

        if not os.path.exists(self.file_path):
            print(f"[ERROR] Файл ініціалізації {self.file_path} не знайдено.")
            return

        print(f"[INFO] Синхронізація поточних даних з файлу Excel: {self.file_path}")
        wb = load_workbook(self.file_path, data_only=True)

        data_to_import = {
            'teachers': [],
            'classrooms': [],
            'students': [],
            'disciplines': [],
            'grades': [],
            'schedules': []
        }

        # 1. Читання Викладачів
        if "Викладачі" in wb.sheetnames:
            ws = wb["Викладачі"]
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row and row[0] is not None:
                    data_to_import['teachers'].append({'id': int(row[0]), 'name': str(row[1]), 'department': str(row[2])})

        # 2. Читання Аудиторій
        if "Аудиторії" in wb.sheetnames:
            ws = wb["Аудиторії"]
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row and row[0] is not None:
                    data_to_import['classrooms'].append({'id': int(row[0]), 'room_number': str(row[1]), 'capacity': int(row[2])})

        # 3. Читання Студентів
        if "Студенти" in wb.sheetnames:
            ws = wb["Студенти"]
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row and row[0] is not None:
                    data_to_import['students'].append({
                        'id': int(row[0]),
                        'name': str(row[1]),
                        'specialization': str(row[2]),
                        'course': str(row[3])
                    })

        # 4. Читання Дисциплін (Курсів)
        discipline_sheet = "Дисципліни" if "Дисципліни" in wb.sheetnames else ("Курси" if "Курси" in wb.sheetnames else None)
        if discipline_sheet:
            ws = wb[discipline_sheet]
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row and row[0] is not None:
                    data_to_import['disciplines'].append({'id': int(row[0]), 'title': str(row[1]), 'teacher_name': str(row[2])})

        # 5. Читання Оцінок
        if "Оцінки" in wb.sheetnames:
            ws = wb["Оцінки"]
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row and row[0] is not None:
                    data_to_import['grades'].append({'id': int(row[0]), 'student_name': str(row[1]), 'discipline_title': str(row[2]), 'value': int(row[3])})

        # 6. Читання Розкладу
        if "Розклад" in wb.sheetnames:
            ws = wb["Розклад"]
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row and row[0] is not None:
                    data_to_import['schedules'].append({
                        'id': int(row[0]),
                        'day_of_week': str(row[1]),
                        'time_slot': str(row[2]),
                        'discipline_title': str(row[3]),
                        'room_number': str(row[4]),
                        'specialization': str(row[5]) if len(row) > 5 and row[5] else "Загальна",
                        'course': str(row[6]) if len(row) > 6 and row[6] else "1"
                    })

        try:
            repository.upload_initial_data(data_to_import)
            print("[SUCCESS] Синхронізацію Excel -> БД успішно виконано.")
        except Exception as e:
            print(f"[CRITICAL] Помилка пакетного збереження: {e}")

    def sync_all_data(self) -> None:
        """Вивантаження поточного стану всіх таблиць бази даних у файл Excel."""
        from storage.db_repository import repository  # Локальний імпорт проти циклічності
        wb = self._get_workbook()

        # 1. Студенти
        students = repository.students.get_all()
        self._export_sheet(wb, "Студенти", ["ID", "ПІБ", "Спеціальність", "Курс"],
                           [[s.id, s.name, s.specialization, s.course] for s in students])

        # 2. Викладачі
        teachers = repository.teachers.get_all()
        self._export_sheet(wb, "Викладачі", ["ID", "ПІБ", "Кафедра"],
                           [[t.id, t.name, t.department] for t in teachers])

        # 3. Дисципліни
        disciplines = repository.get_disciplines_with_details()
        self._export_sheet(wb, "Дисципліни", ["ID", "Назва дисципліни", "Викладач"],
                           [[d.id, d.title, d.teacher.name if d.teacher else "Невідомо"] for d in disciplines])

        # 4. Аудиторії
        classrooms = repository.classrooms.get_all()
        self._export_sheet(wb, "Аудиторії", ["ID", "Номер аудиторії", "Місткість"],
                           [[r.id, r.room_number, r.capacity] for r in classrooms])

        # 5. Оцінки
        grades = repository.get_grades_with_details()
        self._export_sheet(wb, "Оцінки", ["ID", "Студент", "Дисципліна", "Оцінка"],
                           [[g.id, g.student.name if g.student else "Невідомо",
                             g.discipline.title if g.discipline else "Невідомо", g.value] for g in grades])

        # 6. Розклад
        schedules = repository.get_full_schedule()
        self._export_sheet(wb, "Розклад", ["ID", "День тижня", "Час", "Дисципліна", "Аудиторія", "Спеціальність", "Курс"],
                           [[s.id, s.day_of_week, s.time_slot,
                             s.discipline.title if s.discipline else "Невідомо",
                             f"Ауд. {s.classroom.room_number}" if s.classroom else "Невідомо",
                             s.specialization, s.course]
                            for s in schedules])

        if "Sheet" in wb.sheetnames and len(wb.sheetnames) > 1:
            wb.remove(wb["Sheet"])

        wb.save(self.file_path)


excel_handler = ExcelHandler(EXCEL_PATH)