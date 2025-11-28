import subprocess
import time
import os
import psutil
import sys
import ctypes
from ctypes import wintypes

sys.path.append(r"C:\Users\Вадим\Documents\python\trade-brain-main")
import config

class Quik_START_Launcher:
    def __init__(self):
        # Настройки Quik
        self.quik_path = config.quik_path
        self.quik_dir = os.path.dirname(self.quik_path)

        self.password = config.quik_password
        self.account_number = config.quik_account_number


    def stop_quik(self):
        import pyautogui
        time.sleep(5)
        pyautogui.hotkey('Alt', 'f4')

    def start_quik(self):
        try:

            # Запускаем QUIK
            self.quik_process = subprocess.Popen([self.quik_path], cwd=self.quik_dir)
            time.sleep(15)  # Ждем загрузки
            import pyautogui
            pyautogui.hotkey('ctrl', 'q')
            pyautogui.write(self.password) # Вводим пароль
            time.sleep(2)
            pyautogui.press('enter')
            time.sleep(8)
            pyautogui.hotkey('Alt', 'f4')
            time.sleep(10)
            print("QUIK стабилен")
            return True

        except Exception as e:
            print(f"Ошибка при запуске Quik: {e}")
            return False

launcher_quik = Quik_START_Launcher()


def quik_main():
    try:
        launcher_quik.start_quik()
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    quik_main()