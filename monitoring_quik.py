import os

class Monitoring_QUIK:
    def __init__(self):
        self.file_path = 'C:/QUIK_DATA/price.txt'
        self.setup_environment()

    def setup_environment(self):
        """Настройка окружения"""
        directory = os.path.dirname(self.file_path)
        # Если нет дерриктории тогда создаем ее
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✓ Создана директория: {directory}")

        # Если нет папки тогда создаем ее
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write("")
            print(f"✓ Создан файл: {self.file_path}")

        print(f"✓ Файл для мониторинга: {self.file_path}")

    def read_prices(self):
        """Чтение цен из файла"""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r', encoding='utf-8') as file:
                    content = file.read().strip()

                    if content:
                        # Ожидаем формат: GLDRUBF:цена IMOEXF:цена
                        prices = {}
                        parts = content.split()
                        for part in parts:
                            if ':' in part:
                                symbol, price_str = part.split(':', 1)
                                prices[symbol] = float(price_str)
                        return prices

            return False

        except Exception as e:
            print(f"Ошибка чтения файла: {e}")
            return False

MQ = Monitoring_QUIK()
def main():
    settings_search = Monitoring_QUIK()
    a = settings_search.read_prices()
    print(a)

if __name__ == "__main__":
    main()

