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
        self.account_number = "FZQU337843A"

        self.quik_process = None
        self.calculator_process = None
        self.is_running = True
        self.last_clear_date = None

    def is_quik_running(self):
        """Проверяет, запущен ли Quik"""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'info.exe' in proc.info['name'].lower() or 'quik' in proc.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def clear_executive_file(self):
        """Очищает файл executive.txt в конце рабочего дня"""
        try:
            executive_file = "C:/QUIK_DATA/executive.txt"
            current_time = datetime.datetime.now().time()
            end_of_day = datetime.time(23, 50)  # 23:50 - очистка за 10 минут до полуночи

            # Проверяем, нужно ли очистить файл
            if current_time >= end_of_day:
                today = datetime.datetime.now().date()

                # Если еще не очищали сегодня
                if self.last_clear_date != today:
                    if os.path.exists(executive_file):
                        # Сохраняем backup перед очисткой
                        backup_file = f"C:/QUIK_DATA/executive_backup_{today.strftime('%Y%m%d')}.txt"
                        if os.path.exists(executive_file):
                            with open(executive_file, 'r', encoding='utf-8') as src:
                                content = src.read()
                            with open(backup_file, 'w', encoding='utf-8') as dst:
                                dst.write(content)

                        # Очищаем файл
                        open(executive_file, 'w', encoding='utf-8').close()
                        self.last_clear_date = today
                        logger.info(f"✅ Файл executive.txt очищен в конце рабочего дня. Backup: {backup_file}")
                    else:
                        # Создаем пустой файл если не существует
                        open(executive_file, 'w', encoding='utf-8').close()
                        self.last_clear_date = today
                        logger.info("✅ Создан пустой файл executive.txt")
            else:
                # Убедимся что файл существует
                if not os.path.exists(executive_file):
                    open(executive_file, 'w', encoding='utf-8').close()
                    logger.info("✅ Создан пустой файл executive.txt")

        except Exception as e:
            logger.error(f"❌ Ошибка при очистке executive.txt: {e}")

    def check_trading_session(self):
        """Проверяет, идет ли торговая сессия"""
        current_time = datetime.datetime.now().time()
        session_start = datetime.time(7, 0)   # 7:00
        session_end = datetime.time(23, 50)   # 23:50

        return session_start <= current_time <= session_end

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

    def start_calculator(self):
        """Запускает калькулятор сделок"""
        try:
            logger.info("Запускаем калькулятор сделок...")
            self.calculator_process = subprocess.Popen([
                sys.executable, "executive_calculator.py"
            ])
            logger.info("✅ Калькулятор сделок запущен")
            return True
        except Exception as e:
            logger.error(f"Ошибка запуска калькулятора: {e}")
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

        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'info.exe' in proc.info['name'].lower() or 'quik' in proc.info['name'].lower():
                    logger.info(f"Найден процесс Quik: PID {proc.info['pid']}")
                    proc.terminate()
                    proc.wait(timeout=10)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                continue

        logger.info("Quik остановлен")

    def stop_calculator(self):
        """Останавливает калькулятор"""
        if self.calculator_process and self.calculator_process.poll() is None:
            self.calculator_process.terminate()
            self.calculator_process.wait(timeout=5)
            logger.info("Калькулятор остановлен")

    async def stop_all(self):
        """Останавливает все процессы"""
        self.is_running = False
        self.stop_calculator()
        self.stop_quik()

        # Очищаем executive.txt при остановке
        self.clear_executive_file()

        logger.info("Все процессы остановлены")

    async def run_continuous(self):
        """Основной цикл работы"""
        logger.info("=== АВТОМАТИЧЕСКИЙ ЗАПУСК ТОРГОВОЙ СИСТЕМЫ ===")
        logger.info(f"Дата запуска: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")

        while self.is_running:
            try:
                # Проверяем и очищаем executive.txt
                self.clear_executive_file()

                # Проверяем торговую сессию
                if not self.check_trading_session():
                    logger.info("⏸ Сейчас не торговая сессия. Ожидание...")
                    await asyncio.sleep(60)  # Проверяем каждые 5 минут
                    continue

                # Запускаем Quik
                if not self.is_quik_running():
                    self.start_quik()

                # Запускаем калькулятор
                self.start_calculator()

                logger.info("СИСТЕМА ЗАПУЩЕНА")
                logger.info("✓ Quik")
                logger.info("✓ Калькулятор сделок + Двухуровневая стратегия")
                logger.info("✓ Автообновление баланса Finam")

                # Работаем до остановки
                while self.is_running and self.check_trading_session():
                    # Проверяем очистку файла каждую минуту
                    self.clear_executive_file()

                    status_quik = "🟢" if self.is_quik_running() else "🔴"
                    status_calc = "🟢" if self.calculator_process and self.calculator_process.poll() is None else "🔴"

                    if datetime.datetime.now().minute % 30 == 0:
                        logger.info(f"Статус: Quik {status_quik} | Calc {status_calc} | Время: {datetime.datetime.now().strftime('%H:%M')}")

                    await asyncio.sleep(60)

                # Если вышли из цикла из-за окончания сессии
                if self.is_running and not self.check_trading_session():
                    logger.info("🕒 Торговая сессия завершена. Останавливаем процессы...")
                    self.stop_calculator()
                    self.stop_quik()
                    # Очищаем executive.txt
                    self.clear_executive_file()
                    logger.info("💤 Ожидаем начала следующей торговой сессии...")
                    await asyncio.sleep(300)  # Проверяем каждые 5 минут

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
        await asyncio.sleep(30)
        await main()

if __name__ == "__main__":
    print("=== 🚀 AUTOMATIC TRADING SYSTEM ===")
    print("Запуск системы...")
    print("Компоненты: Quik + Calculator + TwoLevel Strategy")
    print("Торговая сессия: 7:00 - 23:50")
    print("Executive.txt очищается автоматически в 23:50")
    print("Для остановки нажмите Ctrl+C")
    print("Логи пишутся в trading_bot.log")
    print("-" * 50)

    asyncio.run(main())