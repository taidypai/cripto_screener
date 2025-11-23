# main_launcher.py
import subprocess
import time
import os
import datetime
import psutil
import sys
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TradingBotLauncher:
    def __init__(self):
        # Настройки Quik
        self.quik_path = r"C:\QuikFinam\info.exe"
        self.quik_dir = os.path.dirname(self.quik_path)
        self.password = "Vados77789878"
        self.account_number = "FZQU337161A"

        # Настройки скриптов
        self.detector_script = "detector.py"

        self.quik_process = None
        self.detector_process = None
        self.is_running = True

    def is_quik_running(self):
        """Проверяет, запущен ли Quik"""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'info.exe' in proc.info['name'].lower() or 'quik' in proc.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def is_detector_running(self):
        """Проверяет, запущен ли detector.py"""
        if self.detector_process and self.detector_process.poll() is None:
            return True
        return False

    def start_quik(self):
        """Запускает Quik и вводит учетные данные"""

        if self.is_quik_running():
            logger.info("Quik уже запущен")
            return True

        if not os.path.exists(self.quik_path):
            logger.error(f"Файл Quik не найден: {self.quik_path}")
            return False

        try:
            import pyautogui
            logger.info("Запускаем Quik...")
            self.quik_process = subprocess.Popen([self.quik_path], cwd=self.quik_dir)

            # Ждем пока откроется окно ввода пароля
            logger.info("Ожидаем окно ввода пароля...")
            time.sleep(10)  # Увеличил время ожидания

            # Импортируем pyautogui для эмуляции ввода
            import pyautogui

            # Вводим пароль
            logger.info(f"Вводим пароль")
            pyautogui.write(self.password)
            time.sleep(5)
            pyautogui.press('enter')
            pyautogui.press('tab')

            # Ждем появления следующего окна
            logger.info("Ожидаем следующее окно...")
            time.sleep(8)

            # Вводим номер счета
            logger.info(f"Вводим номер счета")
            pyautogui.write(self.account_number)
            time.sleep(2)
            pyautogui.press('enter')

            logger.info("Quik запущен и учетные данные введены!")
            return True

        except Exception as e:
            logger.error(f"Ошибка при запуске Quik: {e}")
            return False

    def start_detector(self):
        """Запускает скрипт detector.py"""
        try:
            if os.path.exists(self.detector_script):
                logger.info("Запускаем detector.py...")
                self.detector_process = subprocess.Popen([sys.executable, self.detector_script])
                logger.info("Detector.py запущен")
                return True
            else:
                logger.error(f"Файл {self.detector_script} не найден")
                return False
        except Exception as e:
            logger.error(f"Ошибка при запуске detector.py: {e}")
            return False

    def stop_quik(self):
        """Останавливает Quik"""
        logger.info("Останавливаем Quik...")

        try:
            if self.quik_process and self.quik_process.poll() is None:
                self.quik_process.terminate()
                self.quik_process.wait(timeout=10)
        except:
            pass

        # Ищем процессы Quik
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'info.exe' in proc.info['name'].lower() or 'quik' in proc.info['name'].lower():
                    logger.info(f"Найден процесс Quik: PID {proc.info['pid']}")
                    proc.terminate()
                    proc.wait(timeout=10)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                continue

        logger.info("Quik остановлен")

    def stop_detector(self):
        """Останавливает detector.py"""
        logger.info("Останавливаем detector.py...")

        try:
            if self.detector_process and self.detector_process.poll() is None:
                self.detector_process.terminate()
                self.detector_process.wait(timeout=5)
                logger.info("Detector.py остановлен")
        except Exception as e:
            logger.error(f"Ошибка при остановке detector.py: {e}")

    def stop_all(self):
        """Останавливает все процессы"""
        self.is_running = False
        self.stop_detector()
        self.stop_quik()
        logger.info("Все процессы остановлены")

    def wait_until_time(self, target_hour, target_minute=0):
        """Ожидает до указанного времени"""
        while self.is_running:
            now = datetime.datetime.now()
            target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)

            if now >= target_time:
                break

            sleep_time = (target_time - now).total_seconds()
            if sleep_time > 300:  # 5 минут
                logger.info(f"Ожидаем {target_hour:02d}:{target_minute:02d}... осталось {sleep_time/60:.1f} минут")
                time.sleep(300)
            elif sleep_time > 60:  # 1 минута
                time.sleep(60)
            else:
                time.sleep(1)

    def monitor_processes(self):
        """Мониторит процессы и перезапускает при необходимости"""
        while self.is_running:
            try:
                # Проверяем Quik каждые 30 секунд
                if not self.is_quik_running() and self.is_running:
                    logger.warning("Quik не запущен, перезапускаем...")
                    self.start_quik()
                    time.sleep(10)

                # Проверяем detector.py каждые 30 секунд
                if not self.is_detector_running() and self.is_running:
                    logger.warning("Detector.py не запущен, перезапускаем...")
                    self.start_detector()

                time.sleep(30)

            except Exception as e:
                logger.error(f"Ошибка в мониторинге процессов: {e}")
                time.sleep(60)

    def run_continuous(self):
        """Основной цикл работы - запускается один раз и работает всегда"""
        logger.info("=== АВТОМАТИЧЕСКИЙ ЗАПУСК ТОРГОВОГО БОТА ===")
        logger.info(f"Дата запуска: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        logger.info("Режим: непрерывная работа")

        import threading

        # Запускаем мониторинг процессов в отдельном потоке
        monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
        monitor_thread.start()

        while self.is_running:
            try:
                # Ожидаем до 9:00 утра
                logger.info("ОЖИДАЕМ 9:00 УТРА ДЛЯ ЗАПУСКА...")
                self.wait_until_time(9, 0)

                if not self.is_running:
                    break

                logger.info("НАЧАЛО РАБОЧЕГО ДНЯ - ЗАПУСКАЕМ СИСТЕМУ...")

                # Запускаем Quik
                if not self.is_quik_running():
                    self.start_quik()

                # Ждем пока Quik полностью загрузится
                time.sleep(8)

                # Запускаем detector.py
                if not self.is_detector_running():
                    self.start_detector()

                logger.info("СИСТЕМА ЗАПУЩЕНА - РАБОТАЕМ ДО 00:00")

                # Работаем до 00:00
                now = datetime.datetime.now()
                end_time = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)

                while datetime.datetime.now() < end_time and self.is_running:
                    # Каждые 30 минут пишем статус
                    if datetime.datetime.now().minute % 30 == 0:
                        status_quik = "" if self.is_quik_running() else "🔴"
                        status_detector = "" if self.is_detector_running() else "🔴"
                        remaining = (end_time - datetime.datetime.now()).total_seconds() / 3600
                        logger.info(f"Статус: Quik {status_quik} | Detector {status_detector} | До 00:00: {remaining:.1f}ч")

                    time.sleep(60)  # Проверяем каждую минуту

                # Если дошли до 00:00 - останавливаем на ночь
                if self.is_running:
                    logger.info("КОНЕЦ РАБОЧЕГО ДНЯ - ОСТАНАВЛИВАЕМ СИСТЕМУ...")
                    self.stop_detector()
                    self.stop_quik()

                    logger.info("ОТДЫХ ДО ЗАВТРА...")
                    time.sleep(10)  # Короткая пауза перед следующим циклом

            except KeyboardInterrupt:
                logger.info("⏹Остановлено пользователем")
                self.stop_all()
                break
            except Exception as e:
                logger.error(f"Критическая ошибка: {e}")
                logger.info("Перезапуск через 60 секунд...")
                time.sleep(60)

def main():
    """Главная функция - запускает все и работает вечно"""
    launcher = TradingBotLauncher()

    # Обработка Ctrl+C для graceful shutdown
    try:
        launcher.run_continuous()
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки...")
        launcher.stop_all()
    except Exception as e:
        logger.error(f"Фатальная ошибка: {e}")
        logger.info("Перезапуск через 30 секунд...")
        time.sleep(30)
        main()  # Рекурсивный перезапуск

if __name__ == "__main__":
    print("=== 🚀 AUTOMATIC TRADING BOT ===")
    print("Запуск системы...")
    print("Для остановки нажмите Ctrl+C")
    print("Логи пишутся в trading_bot.log")
    print("-" * 50)

    main()
