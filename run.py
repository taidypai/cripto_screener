import asyncio
import threading
import time
from order_block_detector import OrderBlockDetector

class DetectorManager:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.active_detectors = {}

    def start_detector(self, timeframe):
        """Запускает детектор для конкретного таймфрейма"""
        print(f"🚀 Запуск детектора для таймфрейма {timeframe}")

        # Создаем детектор
        detector = OrderBlockDetector(
            timeframe=timeframe,
            bot_token=self.bot_token,
            chat_id=self.chat_id
        )

        # Запускаем в отдельном потоке
        def run_detector():
            asyncio.run(detector.start_detection())

        thread = threading.Thread(target=run_detector, daemon=True)
        thread.start()

        self.active_detectors[timeframe] = {
            'detector': detector,
            'thread': thread
        }

        return thread

def main():
    # Настройки
    BOT_TOKEN = "8442684870:AAEwtD81q4QbQSL5D7fnGUYY7wiOkODAHGM"
    CHAT_ID = "1112634401"

    # Таймфреймы для мониторинга
    TIMEFRAMES = ['5m', '15m', '1h', '4h', '1d']

    # Создаем менеджер
    manager = DetectorManager(BOT_TOKEN, CHAT_ID)

    print("🎯 Запуск системы мониторинга ордерблоков")
    print(f"📊 Таймфреймы: {', '.join(TIMEFRAMES)}")
    print("=" * 50)

    # Запускаем детекторы для каждого таймфрейма
    threads = []
    for timeframe in TIMEFRAMES:
        thread = manager.start_detector(timeframe)
        threads.append(thread)
        print(f"✅ Запущен мониторинг для {timeframe}")
        time.sleep(1)  # Небольшая задержка между запусками

    print("\nВсе детекторы запущены! Система работает...")
    print("Для остановки нажмите Ctrl+C\n")

    # Главный поток ждет завершения (или Ctrl+C)
    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print("\n🛑 Остановка системы...")
        print("👋 До свидания!")

if __name__ == "__main__":
    main()