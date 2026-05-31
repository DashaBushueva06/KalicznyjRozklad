"""
Модуль для роботи з документами Excel за допомогою openpyxl.
Забезпечує експорт актуального стану бази даних у файл init_data.xlsx.
"""

import os
import zipfile
from openpyxl import load_workbook, Workbook
from config.settings import EXCEL_PATH
from storage.db_repository import repository


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

    def sync_all_data(self) -> None:
        """Вивантаження поточного стану всіх таблиць бази даних у файл Excel."""
        wb = self._get_workbook()

        # 1. Студенти
        students = repository.students.get_all()
        self._export_sheet(wb, "Студенти", ["ID", "ПІБ", "Група"],
                           [[s.id, s.name, s.group_id] for s in students])

        # 2. Викладачі
        teachers = repository.teachers.get_all()
        self._export_sheet(wb, "Викладачі", ["ID", "ПІБ", "Кафедра"],
                           [[t.id, t.name, t.department] for t in teachers])

        # 3. Курси
        courses = repository.get_courses_with_details()
        self._export_sheet(wb, "Курси", ["ID", "Назва курсу", "Викладач"],
                           [[c.id, c.title, c.teacher.name if c.teacher else "Невідомо"] for c in courses])

        # 4. Аудиторії
        classrooms = repository.classrooms.get_all()
        self._export_sheet(wb, "Аудиторії", ["ID", "Корпус", "Номер", "Місткість"],
                           [[r.id, r.building, r.room_number, r.capacity] for r in classrooms])

        # 5. Оцінки
        grades = repository.get_grades_with_details()
        self._export_sheet(wb, "Оцінки", ["ID", "Студент", "Курс", "Оцінка"],
                           [[g.id, g.student.name if g.student else "Невідомо",
                             g.course.title if g.course else "Невідомо", g.value] for g in grades])

        # 6. Розклад
        schedules = repository.get_full_schedule()
        self._export_sheet(wb, "Розклад", ["ID", "День", "Час", "Курс", "Аудиторія"],
                           [[s.id, s.day_of_week, s.time_slot,
                             s.course.title if s.course else "Невідомо",
                             f"Корпус {s.classroom.building}, Ауд. {s.classroom.room_number}" if s.classroom else "Невідомо"]
                            for s in schedules])

        # Видалення стандартного порожнього аркуша
        if "Sheet" in wb.sheetnames and len(wb.sheetnames) > 1:
            wb.remove(wb["Sheet"])

        wb.save(self.file_path)


excel_handler = ExcelHandler(EXCEL_PATH)