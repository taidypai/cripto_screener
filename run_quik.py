import subprocess
import time
import os
import datetime
import psutil
import signal

def open_quik_with_credentials():
    # Путь к Quik
    quik_path = r"C:\QuikFinam\info.exe"
    quik_dir = os.path.dirname(quik_path)

    # Учетные данные
    PASSWORD = "Vados77789878"
    ACCOUNT_NUMBER = "FZQU337161A"

    if not os.path.exists(quik_path):
        print(f"Ошибка: Файл Quik не найден по пути: {quik_path}")
        return None

    try:
        print("Запускаем Quik...")
        print(f"Рабочая папка: {quik_dir}")

        # Запускаем Quik с правильной рабочей папкой
        process = subprocess.Popen([quik_path], cwd=quik_dir)

        # Ждем пока откроется окно ввода пароля
        print("Ожидаем окно ввода пароля...")
        time.sleep(8)

        import pyautogui

        # Вводим пароль
        print(f"Вводим пароль: {PASSWORD}")
        pyautogui.write(PASSWORD)
        time.sleep(5)
        pyautogui.press('enter')
        pyautogui.press('tab')

        # Ждем появления следующего окна
        print("Ожидаем следующее окно...")
        time.sleep(8)

        # Вводим номер счета
        print(f"Вводим номер счета: {ACCOUNT_NUMBER}")
        pyautogui.write(ACCOUNT_NUMBER)
        time.sleep(2)
        pyautogui.press('enter')

        print("✅ Quik запущен и учетные данные введены!")
        return process

    except Exception as e:
        print(f"❌ Произошла ошибка: {e}")
        return None

def close_quik():
    """Закрывает Quik"""
    print("Закрываем Quik...")

    # Ищем процессы Quik
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if 'info.exe' in proc.info['name'].lower() or 'quik' in proc.info['name'].lower():
                print(f"Найден процесс Quik: PID {proc.info['pid']}")
                proc.terminate()
                proc.wait(timeout=10)
                print("✅ Quik закрыт")
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            continue

    print("Процесс Quik не найден или не может быть закрыт")
    return False

def calculate_sleep_time():
    """Вычисляет время до 9:00 следующего дня"""
    now = datetime.datetime.now()

    # Время запуска (9:00)
    target_time = now.replace(hour=9, minute=0, second=0, microsecond=0)

    # Если сейчас уже после 9 утра, планируем на завтра
    if now >= target_time:
        target_time += datetime.timedelta(days=1)

    sleep_seconds = (target_time - now).total_seconds()

    print(f"Следующий запуск в: {target_time.strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"Ожидание: {sleep_seconds:.0f} секунд ({sleep_seconds/3600:.1f} часов)")

    return sleep_seconds

def calculate_work_time():
    """Вычисляет время работы до 00:00"""
    now = datetime.datetime.now()

    # Время завершения (00:00 следующего дня)
    end_time = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)

    work_seconds = (end_time - now).total_seconds()

    print(f"Завершение работы в: {end_time.strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"Время работы: {work_seconds:.0f} секунд ({work_seconds/3600:.1f} часов)")

    return work_seconds

def wait_until_target_time(target_hour, target_minute=0):
    """Ожидает до указанного времени"""
    while True:
        now = datetime.datetime.now()
        target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)

        if now >= target_time:
            break

        sleep_time = (target_time - now).total_seconds()
        if sleep_time > 60:  # Обновляем сообщение каждую минуту
            print(f"⏰ Ожидаем {target_hour:02d}:{target_minute:02d}... осталось {sleep_time/60:.1f} минут")
            time.sleep(60)
        else:
            time.sleep(1)

def main_scheduler():
    """Основной планировщик"""
    print("=== ПЛАНИРОВЩИК AUTOMATIC QUIK ===")
    print(f"Дата запуска: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")

    while True:
        try:
            # Ожидаем до 9:00
            print("\n" + "="*50)
            print("ОЖИДАЕМ 9:00 УТРА...")
            wait_until_target_time(9, 0)

            # Запускаем Quik
            print("\nЗАПУСКАЕМ QUIK...")
            quik_process = open_quik_with_credentials()

            if quik_process:
                # Ждем до 00:00
                print("\nРАБОТАЕМ ДО 00:00...")
                work_seconds = calculate_work_time()

                # Ждем либо завершения времени, либо завершения процесса
                start_time = time.time()
                while time.time() - start_time < work_seconds:
                    # Проверяем жив ли процесс Quik
                    if quik_process.poll() is not None:
                        print("Quik завершился раньше времени")
                        break

                    # Обновляем статус каждые 5 минут
                    elapsed = time.time() - start_time
                    remaining = work_seconds - elapsed
                    if int(elapsed) % 300 == 0:  # Каждые 5 минут
                        print(f"⏱ Прошло: {elapsed/3600:.1f}ч, осталось: {remaining/3600:.1f}ч")

                    time.sleep(60)  # Проверяем каждую минуту

                # Закрываем Quik
                print("\nЗАВЕРШАЕМ РАБОТУ...")
                close_quik()

                # Даем время на завершение
                time.sleep(5)

            # Пауза перед следующим циклом (на всякий случай)
            time.sleep(10)

        except KeyboardInterrupt:
            print(f"\n Планировщик остановлен пользователем")
            close_quik()
            break
        except Exception as e:
            print(f"Ошибка в планировщике: {e}")
            print("Перезапуск через 60 секунд...")
            time.sleep(60)

def fix_quik_environment():
    """Исправляет окружение для Quik"""
    quik_dir = r"C:\QuikFinam"
    current_dir = os.getcwd()

    print("🔧 Проверяем окружение Quik...")

    required_files = ["OpenSSL_Pr.dll", "ruscrypto.dll"]

    for file in required_files:
        quik_file = os.path.join(quik_dir, file)
        if not os.path.exists(quik_file):
            print(f"⚠️  Файл {file} не найден в папке Quik")

    print(f"📁 Текущая папка: {current_dir}")
    print(f"📁 Папка Quik: {quik_dir}")

if __name__ == "__main__":
    # Проверяем окружение
    fix_quik_environment()
    time.sleep(3)

    # Запускаем основной планировщик
    main_scheduler()