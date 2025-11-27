# executive_calculator.py
import time
import re
import os
import asyncio
from datetime import datetime
from two_level_strategy import TwoLevelStrategy
from finam_balance import update_balance_in_executive

class ExecutiveCalculator:
    def __init__(self):
        self.executive_file = "C:/QUIK_DATA/executive.txt"
        self.instruments = {
            'GLDRUBF': {'step': 0.1, 'step_cost': 0.1, 'lot_price': 2664.45},
            'IMOEXF': {'step': 0.5, 'step_cost': 5, 'lot_price': 6794.2}
        }
        self.strategy = TwoLevelStrategy()
        self.setup_environment()

    def setup_environment(self):
        """Создает директорию и файл если не существуют"""
        directory = os.path.dirname(self.executive_file)
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✓ Создана директория: {directory}")

    def read_executive_file(self):
        """Чтение всего executive файла"""
        try:
            with open(self.executive_file, 'r') as f:
                return f.read()
        except Exception as e:
            print(f"Ошибка чтения executive файла: {e}")
            return ""

    def read_section(self, content, section_name):
        """Чтение секции из файла"""
        match = re.search(r'\[' + section_name + r'\](.*?)(?=\[|$)', content, re.DOTALL)
        return match.group(1).strip() if match else None

    def parse_section(self, content):
        """Парсинг секции в словарь"""
        lines = content.split('\n')
        data = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                data[key.strip()] = value.strip()
        return data

    def get_current_prices(self):
        """Получение текущих цен из строки PRICES в executive.txt"""
        prices = {}
        try:
            content = self.read_executive_file()

            # Ищем строку PRICES:
            for line in content.split('\n'):
                if line.startswith('PRICES:'):
                    # Формат: PRICES:GLDRUBF/цена; IMOEXF/цена
                    prices_data = line.replace('PRICES:', '').strip()

                    # Разделяем по точкам с запятой
                    pairs = prices_data.split(';')

                    for pair_data in pairs:
                        pair_data = pair_data.strip()
                        if '/' in pair_data:
                            symbol, price_str = pair_data.split('/', 1)
                            symbol = symbol.strip()
                            price_str = price_str.strip()

                            try:
                                prices[symbol] = float(price_str)
                            except ValueError:
                                print(f"❌ Ошибка преобразования цены: {symbol} = {price_str}")
                                continue

                    break

            return prices

        except Exception as e:
            print(f"❌ Ошибка получения цен из PRICES: {e}")
            return {}

    async def update_balance_periodically(self):
        """Периодическое обновление баланса"""
        while True:
            try:
                await update_balance_in_executive()
                await asyncio.sleep(60)  # Обновляем баланс каждую минуту
            except Exception as e:
                print(f"Ошибка обновления баланса: {e}")
                await asyncio.sleep(30)

    def monitor_and_calculate(self):
        """Основной цикл мониторинга и расчета"""
        print("🚀 Запуск калькулятора сделок...")

        # Запускаем обновление баланса в отдельном потоке
        import threading
        def run_balance_updater():
            asyncio.run(self.update_balance_periodically())

        balance_thread = threading.Thread(target=run_balance_updater, daemon=True)
        balance_thread.start()

        # Запускаем двухуровневую стратегию
        strategy_thread = threading.Thread(target=self.strategy.monitor_and_process, daemon=True)
        strategy_thread.start()

        print("✅ Все компоненты запущены:")
        print("   - Автообновление баланса Finam")
        print("   - Двухуровневая стратегия")
        print("   - Мониторинг LEVEL и TELEGA сигналов")

        while True:
            try:
                # Основной цикл для других операций
                time.sleep(1)

            except Exception as e:
                print(f"❌ Ошибка в основном цикле: {e}")
                time.sleep(5)

if __name__ == "__main__":
    calculator = ExecutiveCalculator()
    calculator.monitor_and_calculate()