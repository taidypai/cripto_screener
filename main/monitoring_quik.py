# monitoring_quik.py
import os
from executive_calculator import ExecutiveCalculator

class Monitoring_QUIK:
    def __init__(self):
        self.file_path = 'C:/QUIK_DATA/price.txt'
        self.executive_file = 'C:/QUIK_DATA/executive.txt'
        self.calculator = ExecutiveCalculator()
        self.setup_environment()

    def setup_environment(self):
        """Настройка окружения"""
        directory = os.path.dirname(self.file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✓ Создана директория: {directory}")

        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write("")
            print(f"✓ Создан файл: {self.file_path}")

        print(f"✓ Файл для мониторинга: {self.file_path}")

    def read_prices(self):
        """Чтение цен из файла через калькулятор"""
        try:
            return self.calculator.get_current_prices()
        except Exception as e:
            print(f"Ошибка чтения цен через калькулятор: {e}")
            # Fallback к старому методу
            return self.read_prices_fallback()

    def read_prices_fallback(self):
        """Резервный метод чтения цен"""
        try:
            if not os.path.exists(self.file_path):
                return {}

            with open(self.file_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()

                if not content:
                    return {}

                # Ожидаем формат: GLDRUBF:цена IMOEXF:цена
                prices = {}
                parts = content.split()
                for part in parts:
                    if ':' in part:
                        symbol, price_str = part.split(':', 1)
                        try:
                            prices[symbol] = float(price_str)
                        except ValueError:
                            continue

                return prices

        except Exception:
            return {}

    def get_executive_data(self):
        """Получение данных из executive.txt"""
        try:
            return self.calculator.read_executive_file()
        except Exception as e:
            print(f"Ошибка чтения executive файла: {e}")
            return {}

MQ = Monitoring_QUIK()

def main():
    settings_search = Monitoring_QUIK()
    a = settings_search.read_prices()
    print("Текущие цены:", a)

    executive_data = settings_search.get_executive_data()
    print("Данные executive:", executive_data)

if __name__ == "__main__":
    main()