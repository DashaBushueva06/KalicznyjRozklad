import socket
import json

ALLOWED_TABLES = ['students', 'teachers', 'courses', 'grades', 'rooms', 'schedule']


def send_request(request_data):
    try:
        # Безпечне підключення без таймаутів
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', 8876))

        # Відправляємо запит
        client.sendall((json.dumps(request_data) + "\n").encode('utf-8'))

        # Читаємо відповідь через текстовий буфер
        f = client.makefile('r', encoding='utf-8')
        response_str = f.readline()
        f.close()
        client.close()

        if not response_str:
            return {"status": "error", "message": "Сервер розірвав з'єднання або перезапускається."}

        return json.loads(response_str.strip())

    except ConnectionRefusedError:
        return {"status": "error", "message": "Не вдалося підключитися. Перевірте, чи запущено server.py!"}
    except Exception as e:
        return {"status": "error", "message": f"Мережева помилка ({e}). Спробуйте ще раз."}


def choose_table():
    print("\nДоступні таблиці:")
    for i, table in enumerate(ALLOWED_TABLES, 1):
        print(f"  {i}. {table}")

    while True:
        choice = input("👉 Оберіть номер таблиці (1-6) або '0' для відміни: ").strip()
        if choice == '0':
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(ALLOWED_TABLES):
            return ALLOWED_TABLES[int(choice) - 1]
        print("❌ Невірний вибір. Введіть цифру від 1 до 6.")


def get_validated_input(col_name, is_update=False):
    while True:
        prompt = f"  Нове значення '{col_name}': " if is_update else f"  Введіть {col_name}: "
        val = input(prompt).strip()

        if is_update and not val:
            return val

        if not is_update and not val:
            print("⚠️ Це поле обов'язкове, воно не може бути порожнім!")
            continue

        if col_name == 'grade':
            try:
                num = float(val.replace(',', '.'))
                if 60 <= num <= 100:
                    return str(num)
                else:
                    print("❌ Помилка: Оцінка має бути від 60 до 100!")
            except ValueError:
                print("❌ Помилка: Введіть число!")

        elif col_name.endswith('_id'):
            if val.isdigit():
                return val
            else:
                print(f"❌ Помилка: {col_name} має бути цілим числом (ID)!")
        else:
            return val


def run_console_client():
    while True:
        print("\n" + "=" * 45)
        print("🎓 КЛІЄНТ LMS (Взаємодія із сервером)")
        print("=" * 45)
        print("1. 📖 Переглянути дані")
        print("2. ➕ Додати новий запис")
        print("3. ✏️ Редагувати існуючий запис")
        print("4. ❌ Видалити запис")
        print("5. ⚡ Згенерувати розумний розклад")
        print("0. 🚪 Вийти")
        print("=" * 45)

        choice = input("👉 Оберіть дію (0-5): ").strip()

        if choice == '0':
            print("👋 Роботу завершено. До побачення!")
            break

        elif choice == '1':
            table = choose_table()
            if table:
                res = send_request({"action": "read", "table": table})
                if res.get("status") == "success":
                    data = res.get("data", [])
                    if not data:
                        print("📭 Таблиця порожня.")
                    else:
                        print(f"\n--- Дані таблиці '{table}' ---")
                        for row in data:
                            print(row)
                else:
                    print("❌ Помилка сервера:", res.get("message"))

        elif choice == '2':
            table = choose_table()
            if table:
                col_res = send_request({"action": "get_columns", "table": table})
                if col_res.get("status") == "success" and col_res.get("data"):
                    print(f"\n📝 Заповніть поля для нової фіксації у '{table}':")
                    new_data = {}
                    for col in col_res["data"]:
                        new_data[col] = get_validated_input(col, is_update=False)

                    create_res = send_request({"action": "create", "table": table, "data": new_data})
                    if create_res.get("status") == "success":
                        print("✅ Успіх:", create_res.get("message"))
                    else:
                        print("❌ Відмова сервера:", create_res.get("message"))
                else:
                    print("⚠️ Не вдалося отримати структуру таблиці від сервера.")

        elif choice == '3':
            table = choose_table()
            if table:
                rec_id = input(f"\nВведіть ID запису для зміни у таблиці '{table}': ").strip()
                if not rec_id.isdigit():
                    print("❌ ID має бути числом!")
                    continue

                rec_id = int(rec_id)
                col_res = send_request({"action": "get_columns", "table": table})

                if col_res.get("status") == "success" and col_res.get("data"):
                    print(f"📝 Оновлення (щоб залишити поле без змін — просто натисніть Enter)")
                    update_data = {}
                    for col in col_res["data"]:
                        val = get_validated_input(col, is_update=True)
                        if val: update_data[col] = val

                    if update_data:
                        up_res = send_request({"action": "update", "table": table, "id": rec_id, "data": update_data})
                        if up_res.get("status") == "success":
                            print("✅ Успіх:", up_res.get("message"))
                        else:
                            print("❌ Відмова сервера:", up_res.get("message"))
                    else:
                        print("⚠️ Скасовано: жодних змін не внесено.")

        elif choice == '4':
            table = choose_table()
            if table:
                rec_id = input("\nВведіть ID запису для видалення: ").strip()
                if rec_id.isdigit():
                    del_res = send_request({"action": "delete", "table": table, "id": int(rec_id)})
                    if del_res.get("status") == "success":
                        print("✅ Успіх:", del_res.get("message"))
                    else:
                        print("❌ Відмова сервера:", del_res.get("message"))
                else:
                    print("❌ ID має бути числом!")

        elif choice == '5':
            print("⏳ Сервер аналізує студентів та генерує розклад...")
            res = send_request({"action": "generate_schedule"})
            if res.get("status") == "success":
                print("✅", res.get("message"))
            else:
                print("❌ Помилка сервера:", res.get("message"))

        else:
            print("❌ Оберіть число від 0 до 5.")


if __name__ == "__main__":
    run_console_client()