"""
Модуль для роботи з документами Excel за допомогою openpyxl.
Забезпечує експорт актуального стану бази даних у файл init_data.xlsx
із застосуванням класичного академічного форматування (Times New Roman).
"""

import os
import zipfile
from openpyxl import load_workbook, Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
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
        """Формування окремого аркуша з попереднім видаленням старої версії та стилізацією."""
        if sheet_name in wb.sheetnames:
            std = wb[sheet_name]
            wb.remove(std)

        ws = wb.create_sheet(sheet_name)

        # Вмикаємо відображення сітки (gridlines)
        ws.views.sheetView[0].showGridLines = True

        # СТИЛІЗАЦІЯ ЗА ТВОЇМИ ПАРАМЕТРАМИ
        font_name = "Times New Roman"

        # Заголовки: 14 розмір, жирний, чорний колір тексту
        header_font = Font(name=font_name, size=14, bold=True, color="000000")
        # Легкий сірий фон для шапки, щоб вона відділялася від даних
        header_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")

        # Звичайні клітинки: 12 розмір
        data_font = Font(name=font_name, size=12)

        # Чорні класичні межі таблиці
        black_border = Border(
            left=Side(style='thin', color='000000'),
            right=Side(style='thin', color='000000'),
            top=Side(style='thin', color='000000'),
            bottom=Side(style='thin', color='000000')
        )

        # Вирівнювання
        header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        data_align = Alignment(horizontal="left", vertical="center")
        id_align = Alignment(horizontal="center", vertical="center")

        # 1. Записуємо заголовки
        ws.append(headers)
        ws.row_dimensions[1].height = 28

        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_align
            cell.border = black_border

        # 2. Записуємо дані
        for row_idx, row_data in enumerate(data, start=2):
            ws.append(row_data)
            ws.row_dimensions[row_idx].height = 22

            for col_idx, cell in enumerate(ws[row_idx], start=1):
                cell.font = data_font
                cell.border = black_border

                if col_idx == 1:
                    cell.alignment = id_align
                else:
                    cell.alignment = data_align

        # 3. Автоматичне вирівнювання ширини стовпчиків
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)

            for cell in col:
                if cell.value is not None:
                    max_len = max(max_len, len(str(cell.value)))

            ws.column_dimensions[col_letter].width = max(max_len + 5, 14)

    def sync_all_data(self) -> None:
        """Вивантаження поточного стану всіх таблиць бази даних у файл Excel."""
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

        # 6. Розклад із хронологічним та академічним сортуванням
        schedules = repository.get_full_schedule()

        days_order = {"Понеділок": 1, "Вівторок": 2, "Середа": 3, "Четвер": 4, "П'ятниця": 5}
        time_order = {"08:40 - 10:15": 1, "10:35 - 12:10": 2, "12:20 - 13:55": 3, "14:05 - 15:35": 4}

        def schedule_sort_key(s):
            return (
                s.course or "",
                s.specialization or "",
                days_order.get(s.day_of_week, 6),
                time_order.get(s.time_slot, 5)
            )

        sorted_schedules = sorted(schedules, key=schedule_sort_key)

        self._export_sheet(wb, "Розклад", ["ID", "День тижня", "Час", "Спеціальність", "Курс", "Дисципліна", "Аудиторія"],
                           [[s.id, s.day_of_week, s.time_slot, s.specialization, s.course,
                             s.discipline.title if s.discipline else "Невідомо",
                             f"Ауд. {s.classroom.room_number}" if s.classroom else "Невідомо"]
                            for s in sorted_schedules])

        if "Курси" in wb.sheetnames:
            wb.remove(wb["Курси"])

        if "Sheet" in wb.sheetnames and len(wb.sheetnames) > 1:
            wb.remove(wb["Sheet"])

        wb.save(self.file_path)


# ОЦЕЙ ОБОВ'ЯЗКОВИЙ РЯДОК МАЄ БУТИ НА САМОМУ ПРИКІНЦІ ФАЙЛУ:
excel_handler = ExcelHandler(EXCEL_PATH)