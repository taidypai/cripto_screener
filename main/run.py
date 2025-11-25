# run.py
import subprocess
import time
import os
import datetime
import psutil
import sys
import logging
import asyncio

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

        self.quik_process = None
        self.detector_tasks = []
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

    def start_quik(self):
        """Запускает Quik и вводит учетные данные"""
        if self.is_quik_running():
            logger.info("Quik уже запущен")
            return True

        if not os.path.exists(self.quik_path):
            logger.error(f"Файл Quik не найден: {self.quik_path}")
            return False

        try:
            logger.info("Запускаем Quik...")
            self.quik_process = subprocess.Popen([self.quik_path], cwd=self.quik_dir)

            # Ждем пока откроется окно ввода пароля
            logger.info("Ожидаем окно ввода пароля...")
            time.sleep(15)

            import pyautogui
            # Вводим пароль
            logger.info(f"Вводим пароль")
            pyautogui.write(self.password)
            time.sleep(1)

            # Нажимаем Enter для входа
            pyautogui.press('enter')

            logger.info("✅ Quik запущен и учетные данные введены!")
            time.sleep(15)
            return True

        except Exception as e:
            logger.error(f"Ошибка при запуске Quik: {e}")
            return False

    async def start_detectors(self):
        """Запускает детекторы для всех таймфреймов"""
        from detector import Detector
        from monitoring_quik import MQ

        BOT_TOKEN = "8442684870:AAEwtD81q4QbQSL5D7fnGUYY7wiOkODAHGM"
        CHAT_ID = "1112634401"

        # Тестируем Telegram перед запуском
        test_detector = Detector("test", BOT_TOKEN, CHAT_ID)
        if test_detector.send_telegram_message("🤖 Бот запущен и готов к работе!"):
            logger.info("✅ Тест Telegram прошел успешно")
        else:
            logger.error("❌ Ошибка Telegram! Проверьте токен и chat_id")

        timeframes = ["5m", "15m", "1h"]

        for timeframe in timeframes:
            detector = Detector(timeframe, BOT_TOKEN, CHAT_ID)
            task = asyncio.create_task(detector.start_detection())
            self.detector_tasks.append(task)
            logger.info(f"✅ Запущен детектор для таймфрейма {timeframe}")
            await asyncio.sleep(1)

    def stop_quik(self):
        """Останавливает Quik"""
        logger.info("Останавливаем Quik...")

        try:
            if self.quik_process and self.quik_process.poll() is None:
                self.quik_process.terminate()
                self.quik_process.wait(timeout=10)
        except:
            pass

        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'info.exe' in proc.info['name'].lower() or 'quik' in proc.info['name'].lower():
                    logger.info(f"Найден процесс Quik: PID {proc.info['pid']}")
                    proc.terminate()
                    proc.wait(timeout=10)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                continue

        logger.info("Quik остановлен")

    async def stop_detectors(self):
        """Останавливает все детекторы"""
        logger.info("Останавливаем детекторы...")

        for task in self.detector_tasks:
            task.cancel()

        # Ждем завершения всех задач
        if self.detector_tasks:
            await asyncio.gather(*self.detector_tasks, return_exceptions=True)

        self.detector_tasks = []
        logger.info("Все детекторы остановлены")

    async def stop_all(self):
        """Останавливает все процессы"""
        self.is_running = False
        await self.stop_detectors()
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
            if sleep_time > 300:
                logger.info(f"Ожидаем {target_hour:02d}:{target_minute:02d}... осталось {sleep_time/60:.1f} минут")
                time.sleep(300)
            elif sleep_time > 60:
                time.sleep(60)
            else:
                time.sleep(1)

    async def monitor_processes(self):
        """Мониторит процессы и перезапускает при необходимости"""
        while self.is_running:
            try:
                # Проверяем Quik
                if not self.is_quik_running() and self.is_running:
                    logger.warning("Quik не запущен, перезапускаем...")
                    self.start_quik()

                # Проверяем детекторы
                for i, task in enumerate(self.detector_tasks):
                    if task.done() and self.is_running:
                        logger.warning(f"Детектор упал, перезапускаем...")
                        # Перезапускаем задачу
                        from detector import Detector
                        BOT_TOKEN = "8442684870:AAEwtD81q4QbQSL5D7fnGUYY7wiOkODAHGM"
                        CHAT_ID = "1112634401"

                        timeframe = ["5m", "15m", "1h"][i]
                        detector = Detector(timeframe, BOT_TOKEN, CHAT_ID)
                        new_task = asyncio.create_task(detector.start_detection())
                        self.detector_tasks[i] = new_task

                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Ошибка в мониторинге процессов: {e}")
                await asyncio.sleep(60)

    async def run_continuous(self):
        """Основной цикл работы"""
        logger.info("=== АВТОМАТИЧЕСКИЙ ЗАПУСК ТОРГОВОГО БОТА ===")
        logger.info(f"Дата запуска: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")

        # Запускаем мониторинг процессов
        monitor_task = asyncio.create_task(self.monitor_processes())

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

                # Запускаем детекторы
                await self.start_detectors()

                logger.info("СИСТЕМА ЗАПУЩЕНА - РАБОТАЕМ ДО 23:59")

                # Работаем до 23:59
                end_time = datetime.datetime.now().replace(hour=23, minute=59, second=0, microsecond=0)

                while datetime.datetime.now() < end_time and self.is_running:
                    status_quik = "🟢" if self.is_quik_running() else "🔴"
                    running_detectors = sum(1 for task in self.detector_tasks if not task.done())
                    remaining = (end_time - datetime.datetime.now()).total_seconds() / 60

                    if datetime.datetime.now().minute % 30 == 0:
                        logger.info(f"Статус: Quik {status_quik} | Detectors {running_detectors}/3 | До 23:59: {remaining:.1f} мин")

                    await asyncio.sleep(60)

                # Останавливаем на ночь
                if self.is_running:
                    logger.info("КОНЕЦ РАБОЧЕГО ДНЯ - ОСТАНАВЛИВАЕМ СИСТЕМУ...")
                    await self.stop_detectors()
                    self.stop_quik()
                    logger.info("ОТДЫХ ДО ЗАВТРА...")
                    await asyncio.sleep(60)

            except KeyboardInterrupt:
                logger.info("⏹ Остановлено пользователем")
                await self.stop_all()
                break
            except Exception as e:
                logger.error(f"Критическая ошибка: {e}")
                logger.info("Перезапуск через 60 секунд...")
                await asyncio.sleep(60)

async def main():
    """Главная функция"""
    launcher = TradingBotLauncher()

    try:
        await launcher.run_continuous()
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки...")
        await launcher.stop_all()
    except Exception as e:
        logger.error(f"Фатальная ошибка: {e}")
        logger.info("Перезапуск через 30 секунд...")
        await asyncio.sleep(30)
        await main()

if __name__ == "__main__":
    print("=== 🚀 AUTOMATIC TRADING BOT ===")
    print("Запуск системы...")
    print("Для остановки нажмите Ctrl+C")
    print("Логи пишутся в trading_bot.log")
    print("-" * 50)

    asyncio.run(main())
