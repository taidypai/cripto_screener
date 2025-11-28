from components import start_quik, setup_environment
from components.time_service import timeservice
from liquidity_process import liquid_main
from impuls_process import impuls_main
from trading_engine import trade_main
from components.start_quik import launcher_quik
import asyncio
import datetime
import time
import signal
import sys


class TradingSystem:
    def __init__(self):
        self.is_running = False
        self.current_tasks = []
        self.setup_signal_handlers()

    def setup_signal_handlers(self):
        """Настройка обработчиков сигналов для graceful shutdown"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Обработчик сигналов завершения"""
        print(f"\nПолучен сигнал завершения {signum}. Останавливаем систему...")
        self.is_running = False
        self.stop_all_processes()

    async def run_both_processes(self):
        """Запуск обоих процессов параллельно"""
        print('/ -- Запуск торговых процессов')

        # Создаем задачи
        tasks = [
            asyncio.create_task(liquid_main.liquidity_main(), name="liquidity"),
            asyncio.create_task(impuls_main.impuls_main(), name="impuls"),
            asyncio.create_task(trade_main.trade_main(), name="trading")
        ]

        self.current_tasks = tasks

        try:
            # Ждем завершения всех задач или прерывания
            await asyncio.gather(*tasks, return_exceptions=True)
        except asyncio.CancelledError:
            print("Процессы были отменены")
        except Exception as e:
            print(f"Ошибка в процессах: {e}")
        finally:
            self.current_tasks = []

    def stop_all_processes(self):
        """Принудительная остановка всех процессов"""
        print("Останавливаем все процессы...")
        for task in self.current_tasks:
            if not task.done():
                task.cancel()
        launcher_quik.stop_quik()

    async def trading_session(self):
        """Запускает торговую сессию с 8:00 до 00:00"""
        session_start = datetime.datetime.now()
        print(f"Начало торговой сессии: {session_start.strftime('%H:%M:%S')}")

        while self.is_running and timeservice.is_trading_time():
            current_time = datetime.datetime.now()
            time_until_midnight = timeservice.get_time_until_midnight()

            print(f"Торговая сессия активна. Время: {current_time.strftime('%H:%M:%S')}")
            print(f"До конца сессии: {time_until_midnight}")

            try:
                # Запускаем процессы с таймаутом
                await asyncio.wait_for(self.run_both_processes(), timeout=55.0)
            except asyncio.TimeoutError:
                print("Процессы завершили итерацию, перезапуск...")
            except Exception as e:
                print(f"Ошибка в торговой сессии: {e}")

            # Короткая пауза перед следующей итерацией
            await asyncio.sleep(5)

        print("Торговая сессия завершена")

    async def wait_for_trading_time(self):
        """Ожидание начала торгового времени (8:00)"""
        while self.is_running and not timeservice.is_trading_time():
            current_time = datetime.datetime.now()
            time_until_start = timeservice.get_time_until_trading_start()

            if time_until_start:
                print(f"До начала торгов: {time_until_start}")
            else:
                print(f"Ночное время. Текущее время: {current_time.strftime('%H:%M:%S')}")

            # В ночное время проверяем реже
            await asyncio.sleep(300)  # 5 минут

    def init_main(self):
        """Основная функция инициализации системы"""
        print(" === TRADING SYSTEM === ")
        print('/ -- Настройка рабочей среды')

        try:
            # Инициализация компонентов
            start_quik.quik_main()  # Запуск QUIK
            setup_environment.environment_main()  # Настройка директорий

            self.is_running = True

            # Основной цикл работы системы
            while self.is_running:
                # Ждем начала торгового времени
                asyncio.run(self.wait_for_trading_time())

                if not self.is_running:
                    break

                # Запускаем торговую сессию
                asyncio.run(self.trading_session())

                # Пауза между сессиями
                if self.is_running:
                    print("Переход в режим ожидания до следующей торговой сессии")
                    time.sleep(60)  # 1 минута паузы перед проверкой

        except KeyboardInterrupt:
            print("\n Система остановлена пользователем")
        except Exception as e:
            print(f"Критическая ошибка: {e}")
        finally:
            self.is_running = False
            self.stop_all_processes()
            print("Система завершила работу")


# Глобальный экземпляр системы
trading_system = TradingSystem()

if __name__ == "__main__":
    trading_system.init_main()