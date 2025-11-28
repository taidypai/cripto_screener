# monitoring_quik.py
import os

class Environment:
    def __init__(self):
        self.directory = 'C:/QUIK_DATA/'
        self.files = ['C:/QUIK_DATA/price.txt','C:/QUIK_DATA/order.txt', 'C:/QUIK_DATA/order_list.txt']


    def setup_environment(self):
        if not os.path.exists(self.directory ):
            os.makedirs(self.directory )
            print(f"✓ Создана директория: {self.directory }")
        """Настройка окружения"""
        for file in self.files:
            if not os.path.exists(file):
                with open(file, 'w', encoding='utf-8') as f:
                    f.write("")
                print(f"✓ Создан файл: {file}")

settings = Environment()

def environment_main():
    settings.setup_environment()

if __name__ == "__main__":
    main()