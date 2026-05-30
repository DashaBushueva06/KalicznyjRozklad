import socket
import threading
import json
import sqlite3
import pandas as pd
import os
import random

ALLOWED_TABLES = {'students', 'teachers', 'courses', 'grades', 'rooms', 'schedule'}


class ExcelLMSDatabase:
    def __init__(self, excel_file='lms_data.xlsx'):
        self.excel_file = excel_file
        self.db_lock = threading.Lock()

        self.conn = sqlite3.connect(':memory:', check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.load_from_excel()

    def load_from_excel(self):
        print(f"[СЕРВЕР] Завантаження даних з {self.excel_file}...")
        try:
            if os.path.exists(self.excel_file):
                with pd.ExcelFile(self.excel_file) as excel_file:
                    for sheet in excel_file.sheet_names:
                        if sheet in ALLOWED_TABLES:
                            df = pd.read_excel(self.excel_file, sheet_name=sheet, engine='openpyxl')
                            df.to_sql(sheet, self.conn, if_exists='replace', index=False)
        except Exception as e:
            print(f"[СЕРВЕР] Помилка читання Excel: {e}")

        for table in ALLOWED_TABLES:
            self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {table} (id INTEGER PRIMARY KEY)")
        self.conn.commit()
        print("[СЕРВЕР] Дані успішно завантажені в пам'ять.")

    def sync_to_excel(self):
        try:
            with pd.ExcelWriter(self.excel_file, engine='openpyxl') as writer:
                for table in ALLOWED_TABLES:
                    df = pd.read_sql_query(f"SELECT * FROM {table}", self.conn)
                    df.to_excel(writer, sheet_name=table, index=False)
            print("[СЕРВЕР] ✅ Дані синхронізовано з Excel.")
        except Exception as e:
            print(f"[ПОМИЛКА] Помилка збереження в Excel (закрийте файл!): {e}")

    def get_columns(self, table):
        with self.db_lock:
            self.cursor.execute(f"PRAGMA table_info({table})")
            return [row['name'] for row in self.cursor.fetchall() if row['name'] != 'id']

    def read_table(self, table):
        with self.db_lock:
            self.cursor.execute(f"SELECT * FROM {table}")
            return [dict(row) for row in self.cursor.fetchall()]

    def validate_data(self, table, data, rec_id=None):
        if rec_id is not None:
            self.cursor.execute(f"SELECT 1 FROM {table} WHERE id = ?", (rec_id,))
            if not self.cursor.fetchone():
                raise ValueError(f"Запис з ID {rec_id} у таблиці '{table}' не існує!")

        relationships = {
            'courses': {'teacher_id': 'teachers'},
            'grades': {'student_id': 'students', 'course_id': 'courses'},
            'schedule': {'course_id': 'courses', 'room_id': 'rooms'}
        }

        if table in relationships:
            for field, ref_table in relationships[table].items():
                if field in data and data[field]:
                    try:
                        ref_id = int(data[field])
                    except ValueError:
                        raise ValueError(f"Поле '{field}' має бути числовим ID!")

                    self.cursor.execute(f"SELECT 1 FROM {ref_table} WHERE id = ?", (ref_id,))
                    if not self.cursor.fetchone():
                        raise ValueError(f"Помилка зв'язку: Запису з ID {ref_id} у таблиці '{ref_table}' не існує!")

        if table == 'grades' and 'grade' in data and data['grade']:
            try:
                val = float(str(data['grade']).replace(',', '.'))
                if not (60 <= val <= 100):
                    raise ValueError("Оцінка має бути в межах від 60 до 100!")
            except ValueError:
                raise ValueError("Оцінка має бути числом!")

    def create_record(self, table, data):
        with self.db_lock:
            self.validate_data(table, data)
            cols = ', '.join(data.keys())
            vals = ', '.join(['?'] * len(data))
            query = f"INSERT INTO {table} ({cols}) VALUES ({vals})"
            self.cursor.execute(query, tuple(data.values()))
            self.conn.commit()
            self.sync_to_excel()

    def update_record(self, table, rec_id, data):
        with self.db_lock:
            self.validate_data(table, data, rec_id)
            set_clause = ', '.join([f"{k}=?" for k in data.keys()])
            query = f"UPDATE {table} SET {set_clause} WHERE id=?"
            self.cursor.execute(query, tuple(list(data.values()) + [rec_id]))
            self.conn.commit()
            self.sync_to_excel()

    def delete_record(self, table, rec_id):
        with self.db_lock:
            self.cursor.execute(f"DELETE FROM {table} WHERE id=?", (rec_id,))
            if self.cursor.rowcount == 0:
                raise ValueError(f"Запис з ID {rec_id} у таблиці '{table}' не знайдено.")
            self.conn.commit()
            self.sync_to_excel()

    def generate_schedule(self):
        with self.db_lock:
            # 1. Отримуємо всі дані, включаючи студентів
            self.cursor.execute("SELECT * FROM courses")
            courses = [dict(row) for row in self.cursor.fetchall()]

            self.cursor.execute("SELECT * FROM rooms")
            db_rooms = [dict(row) for row in self.cursor.fetchall()]

            self.cursor.execute("SELECT * FROM students")
            students_list = [dict(row) for row in self.cursor.fetchall()]

            self.cursor.execute("SELECT course_id, student_id FROM grades")
            enrollments = [dict(row) for row in self.cursor.fetchall()]

            if not courses or not db_rooms or not students_list:
                return "Немає курсів, студентів або аудиторій для генерації."

            # Знаходимо колонку, де записана спеціальність (major, group тощо)
            group_col = None
            if students_list:
                for col in ['major', 'group', 'specialty']:
                    if col in students_list[0]:
                        group_col = col
                        break

            # Призначаємо спеціальність кожному студенту
            student_majors = {s['id']: (s[group_col] if group_col else "Загальна група") for s in students_list}

            # 2. Групуємо студентів за курсом ТА СПЕЦІАЛЬНІСТЮ
            course_groups = {}
            all_majors = set()

            for e in enrollments:
                cid = e['course_id']
                sid = e['student_id']
                major = student_majors.get(sid, "Загальна група")

                key = (cid, major)
                if key not in course_groups:
                    course_groups[key] = set()
                course_groups[key].add(sid)
                all_majors.add(major)

            # 3. Перестворюємо таблицю розкладу
            self.cursor.execute("DROP TABLE IF EXISTS schedule")
            self.cursor.execute("""
                                CREATE TABLE schedule
                                (
                                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                                    course_id INTEGER,
                                    room_id   INTEGER,
                                    time_slot TEXT
                                )
                                """)

            days = ["Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця"]
            # Додано 4-ту пару, щоб було куди ставити по 2 пари на день усім групам
            pairs_time = ["08:40 - 10:15", "10:35 - 12:10", "12:20 - 13:55", "14:05 - 15:40"]

            teacher_busy = set()
            room_busy = set()
            student_busy = set()

            # Лічильник: скільки пар у кожної спеціальності в конкретний день
            major_day_load = {m: {d: 0 for d in days} for m in all_majors}

            added = 0
            unplaced = []

            # Перетворюємо у список і перемішуємо, щоб групи оброблялися хаотично
            tasks = list(course_groups.items())
            random.shuffle(tasks)

            # 5. Розумне призначення
            for (c_id, major), c_students in tasks:
                t_id = next((c['teacher_id'] for c in courses if c['id'] == c_id), None)
                if not t_id: continue

                students_count = len(c_students)

                # 💡 УМОВА 1: Кожній спеціальності по 2 пари кожного предмета на тиждень
                sessions_needed = 2
                sessions_scheduled = 0
                attempts = 0

                while sessions_scheduled < sessions_needed and attempts < 150:
                    attempts += 1

                    # 💡 УМОВА 3: Балансуємо дні. Шукаємо дні, де у групи ще менше 2 пар.
                    underloaded_days = [d for d in days if major_day_load[major][d] < 2]
                    day = random.choice(underloaded_days) if underloaded_days else random.choice(days)

                    p_time = random.choice(pairs_time)
                    time_slot = f"{day}, {p_time}"

                    if (t_id, time_slot) in teacher_busy: continue
                    if any((sid, time_slot) in student_busy for sid in c_students): continue

                    # 💡 УМОВА 2: Використовуємо всі кімнати! (Перемішуємо їх список)
                    available_rooms = list(db_rooms)
                    random.shuffle(available_rooms)

                    placed = False
                    for room in available_rooms:
                        r_id = room.get('id')
                        cap_val = room.get('capacity')
                        capacity = int(cap_val) if (cap_val and str(cap_val).strip().isdigit()) else 999

                        if students_count > capacity: continue

                        if (r_id, time_slot) not in room_busy:
                            self.cursor.execute(
                                "INSERT INTO schedule (course_id, room_id, time_slot) VALUES (?, ?, ?)",
                                (c_id, r_id, time_slot)
                            )
                            teacher_busy.add((t_id, time_slot))
                            room_busy.add((r_id, time_slot))
                            for sid in c_students:
                                student_busy.add((sid, time_slot))

                            major_day_load[major][day] += 1
                            added += 1
                            sessions_scheduled += 1
                            placed = True
                            break

                    if placed:
                        attempts = 0  # Скидаємо лічильник після успішного бронювання

                if sessions_scheduled < sessions_needed:
                    unplaced.append(f"Предмет {c_id} (Спец: {major})")

            self.conn.commit()
            self.sync_to_excel()

            msg = f"✨ Розклад згенеровано! Призначено {added} занять по всіх спеціальностях."
            if unplaced:
                msg += f"\n⚠️ УВАГА: Не влізли курси: {', '.join(unplaced)}"
            return msg


class LMSServer:
    def __init__(self, host='127.0.0.1', port=8876):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen()
        self.db = ExcelLMSDatabase()
        print(f"\n🚀 [СЕРВЕР ЗАПУЩЕНО] Очікування підключень за адресою {host}:{port}...\n")

    def handle_client(self, conn, addr):
        with conn:
            try:
                # Читаємо дані як звичайний текстовий потік
                f = conn.makefile('r', encoding='utf-8')
                data = f.readline()
                if not data: return

                req = json.loads(data.strip())
                action = req.get("action")
                table = req.get("table")

                if action == "get_columns":
                    res = {"status": "success", "data": self.db.get_columns(table)}
                elif action == "read":
                    res = {"status": "success", "data": self.db.read_table(table)}
                elif action == "create":
                    self.db.create_record(table, req['data'])
                    res = {"status": "success", "message": "Запис успішно додано!"}
                elif action == "update":
                    self.db.update_record(table, req['id'], req['data'])
                    res = {"status": "success", "message": "Запис успішно оновлено!"}
                elif action == "delete":
                    self.db.delete_record(table, req['id'])
                    res = {"status": "success", "message": "Запис видалено!"}
                elif action == "generate_schedule":
                    msg = self.db.generate_schedule()
                    res = {"status": "success", "message": msg}
                else:
                    res = {"status": "error", "message": f"Невідома команда: {action}"}
            except Exception as e:
                res = {"status": "error", "message": str(e)}

            try:
                conn.sendall((json.dumps(res) + "\n").encode('utf-8'))
            except Exception:
                pass

    def start(self):
        try:
            while True:
                conn, addr = self.server.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
        except KeyboardInterrupt:
            print("\n[СЕРВЕР ЗУПИНЕНО]")


if __name__ == "__main__":
    app = LMSServer()
    app.start()