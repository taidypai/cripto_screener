import asyncio
import logging
import pytz
import datetime
import aiohttp
import requests
import os
import time
from binance.client import Client
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TimeService:
    def __init__(self, use_binance_time=False):
        self.timeframe_minutes = {
            '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '4h': 240, '1d': 1440
        }
        self.use_binance_time = use_binance_time
        self.binance_server_time_diff = 0
        self.last_sync_time = 0

    async def sync_binance_time(self):
        try:
            url = "https://api.binance.com/api/v3/time"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        binance_server_time = data['serverTime'] / 1000
                        local_time = datetime.now().timestamp()
                        self.binance_server_time_diff = binance_server_time - local_time
                        self.last_sync_time = local_time
                        logger.info(f"Synced with Binance time. Diff: {self.binance_server_time_diff:.2f}s")
        except Exception as e:
            logger.error(f"Error syncing with Binance: {e}")

    def get_current_time(self):
        if self.use_binance_time:
            local_time = datetime.now().timestamp()
            if local_time - self.last_sync_time > 3600:
                asyncio.create_task(self.sync_binance_time())

            binance_timestamp = local_time + self.binance_server_time_diff
            return datetime.fromtimestamp(binance_timestamp, pytz.UTC)
        else:
            return datetime.now()

    async def get_time_to_candle_close(self, timeframe):
        now = self.get_current_time()

        if timeframe not in self.timeframe_minutes:
            return 0

        minutes = self.timeframe_minutes[timeframe]
        current_minute = now.minute
        remainder = current_minute % minutes
        minutes_remaining = minutes - remainder

        close_time = now.replace(second=0, microsecond=0) + timedelta(minutes=minutes_remaining)
        seconds_remaining = max(0, int((close_time - now).total_seconds()))

        return seconds_remaining

    async def get_time_to_next_hour(self):
        """Время до начала следующего часа"""
        now = self.get_current_time()
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        seconds_remaining = max(0, int((next_hour - now).total_seconds()))
        return seconds_remaining

    @staticmethod
    async def format_time_remaining(seconds):
        if seconds >= 3600:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        elif seconds >= 60:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes:02d}:{secs:02d}"
        else:
            return f"{seconds:02d}с"

class FilePriceMonitor:
    def __init__(self, file_path="C:/QUIK_DATA/price.txt"):
        self.file_path = file_path
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
        """Чтение цен из файла"""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                    if content:
                        # Ожидаем формат: GLDRUBF:цена IMOEXF:цена NASD:цена
                        prices = {}
                        parts = content.split()
                        for part in parts:
                            if ':' in part:
                                symbol, price_str = part.split(':', 1)
                                if self.is_float(price_str):
                                    prices[symbol] = float(price_str)
                        return prices

            return {}

        except Exception as e:
            logger.error(f"Ошибка чтения файла: {e}")
            return {}

    def is_float(self, value):
        """Проверка что значение можно преобразовать в float"""
        try:
            float(value)
            return True
        except ValueError:
            return False

class OrderBlockDetector:
    def __init__(self, asset_name, timeframe, bot_token, chat_id, price_monitor=None, use_file_data=False):
        self.asset_name = asset_name
        self.timeframe = timeframe
        self.price_monitor = price_monitor
        self.use_file_data = use_file_data
        self.time_service = TimeService(use_binance_time=not use_file_data)
        self.BOT_TOKEN = bot_token
        self.CHAT_ID = chat_id
        self.previous_close = None

        # Инициализация Binance клиента только для криптовалют
        if not use_file_data:
            self.client = Client()

    def send_telegram_message(self, message_text):
        url = f"https://api.telegram.org/bot{self.BOT_TOKEN}/sendMessage"
        data = {'chat_id': self.CHAT_ID, 'text': message_text}

        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                print("✅ Сообщение отправлено в Telegram!")
                return True
            else:
                print(f"❌ Ошибка Telegram: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Ошибка подключения к Telegram: {e}")
            return False

    def get_current_price(self):
        """Получаем текущую цену из файла или Binance"""
        try:
            if self.use_file_data:
                prices = self.price_monitor.read_prices()
                return prices.get(self.asset_name)
            else:
                # Используем Binance API для криптовалют
                price = float(self.client.get_symbol_ticker(symbol=self.asset_name)['price'])
                return price
        except Exception as e:
            logger.error(f"Ошибка получения цены для {self.asset_name}: {e}")
            return None

    def analyze_candle_pattern(self, previous_candle, current_candle):
        prev_change = previous_candle['change']
        curr_change = current_candle['change']

        # Проверяем смену направления и соотношение размеров
        if (prev_change * curr_change < 0) and (abs(curr_change) / abs(prev_change) > 2):
            return "GREEN" if curr_change > 0 else "RED"
        return False

    async def start_detection(self):
        candle_history = []  # Будет хранить последние 2 свечи

        # Определяем тип данных для логов
        asset_type = "ФАЙЛ" if self.use_file_data else "BINANCE"

        print(f"🚀 Запуск сервиса {self.asset_name} {self.timeframe} ({asset_type})")

        # Синхронизируем время для Binance
        if not self.use_file_data:
            await self.time_service.sync_binance_time()

        # Получаем начальную цену для первой свечи
        initial_price = self.get_current_price()
        if initial_price is not None:
            # Создаем "нулевую" свечу для начала
            initial_candle = {
                "open": initial_price,
                "close": initial_price,
                "change": 0
            }
            candle_history.append(initial_candle)
            print(f"📊 Начальная цена {self.asset_name}: {initial_price}")

        try:
            while True:
                wait_time = await self.time_service.get_time_to_candle_close(self.timeframe)

                if wait_time > 1:
                    formatted_time = await self.time_service.format_time_remaining(wait_time)
                    print(f"⏰ {self.asset_name} {self.timeframe}: Ожидание закрытия свечи: {formatted_time}")
                    await asyncio.sleep(wait_time)
                else:
                    await asyncio.sleep(1)
                    continue

                # МОМЕНТ ЗАКРЫТИЯ СВЕЧИ - получаем актуальную цену
                current_price = self.get_current_price()
                if current_price is None:
                    print(f"⚠️ {self.asset_name}: Цена не доступна, пропускаем свечу")
                    continue

                # Определяем цену открытия текущей свечи
                if len(candle_history) > 0:
                    # Цена открытия текущей свечи = цена закрытия предыдущей
                    open_price = candle_history[-1]['close']
                else:
                    open_price = current_price

                # Создаем данные текущей свечи
                current_candle = {
                    "open": open_price,
                    "close": current_price,
                    "change": current_price - open_price
                }

                print(f"🎯 {self.asset_name} {self.timeframe}: Закрытие свечи - Open: {open_price:.2f}, Close: {current_price:.2f}, Change: {current_candle['change']:.2f}")

                # Добавляем текущую свечу в историю
                candle_history.append(current_candle)

                # Ограничиваем историю последними 2 свечами
                if len(candle_history) > 2:
                    candle_history = candle_history[-2:]

                # Анализируем когда есть 2 свечи
                if len(candle_history) == 2:
                    order_block_status = self.analyze_candle_pattern(candle_history[0], candle_history[1])

                    if order_block_status:
                        message = f"{self.asset_name}\nТаймфрейм: {self.timeframe}\nТип: {order_block_status} ({candle_history[0]['change']:+.2f}) → ({candle_history[1]['change']:+.2f})"
                        self.send_telegram_message(message)
                        print(f"✅ {self.asset_name} {self.timeframe}: ОРДЕРБЛОК НАЙДЕН - {order_block_status}")
                    else:
                        print(f"❌ {self.asset_name} {self.timeframe}: Order Block не обнаружен")

        except KeyboardInterrupt:
            print(f"\n📢 Сервис {self.asset_name} {self.timeframe} остановлен")
        except Exception as e:
            print(f"💥 Критическая ошибка в сервисе {self.asset_name} {self.timeframe}: {e}")

async def monitor_file_prices(price_monitor):
    """Функция для мониторинга цен в реальном времени из файла"""
    while True:
        prices = price_monitor.read_prices()
        timestamp = datetime.now().strftime('%H:%M:%S')

        if prices:
            price_display = " | ".join([f"{asset}: {price:>8.2f}" for asset, price in prices.items()])
            print(f"{timestamp} | {price_display}")
        else:
            print(f"{timestamp} | Ожидание данных...")

        await asyncio.sleep(2)

def get_telegram_credentials():
    """Функция для получения токена бота и chat ID через консоль"""
    print("🤖 Введите данные Telegram бота:")
    bot_token = input("Токен бота: ").strip()
    chat_id = input("Chat ID: ").strip()

    if not bot_token or not chat_id:
        print("❌ Ошибка: токен бота и chat ID не могут быть пустыми!")
        return get_telegram_credentials()

    return bot_token, chat_id

async def main():
    # Получаем данные Telegram бота
    BOT_TOKEN, CHAT_ID = get_telegram_credentials()
    print("✅ Данные Telegram бота получены успешно!")

    # Создаем монитор цен для файловых данных
    price_monitor = FilePriceMonitor("C:/QUIK_DATA/price.txt")

    # Создаем сервисы времени
    time_service_binance = TimeService(use_binance_time=True)
    time_service_file = TimeService(use_binance_time=False)

    print("\n⏳ Ожидание начала следующего часа...")

    # Ждем начала следующего часа
    wait_time = await time_service_binance.get_time_to_next_hour()
    if wait_time > 0:
        formatted_time = await time_service_binance.format_time_remaining(wait_time)
        print(f"🕒 До начала следующего часа: {formatted_time}")
        await asyncio.sleep(wait_time)

    print("✅ Начало нового часа, запуск всех детекторов...")

    # СОЗДАЕМ ВСЕ ДЕТЕКТОРЫ АВТОМАТИЧЕСКИ
    detectors = []

    # Криптовалюты (Binance) - все активы на таймфреймах 1h, 4h, 1d
    crypto_assets = ['BTCUSDT', 'ETHUSDT']
    crypto_timeframes = ['1h', '4h', '1d']

    for asset in crypto_assets:
        for timeframe in crypto_timeframes:
            detector = OrderBlockDetector(
                asset_name=asset,
                timeframe=timeframe,
                bot_token=BOT_TOKEN,
                chat_id=CHAT_ID,
                price_monitor=None,
                use_file_data=False
            )
            detectors.append(detector)
            print(f"✅ Создан детектор КРИПТА: {asset} {timeframe}")

    # Файловые данные - все активы на таймфреймах 1h, 4h
    file_assets = ['GLDRUBF', 'IMOEXF', 'NASD']
    file_timeframes = ['1h', '4h']

    for asset in file_assets:
        for timeframe in file_timeframes:
            detector = OrderBlockDetector(
                asset_name=asset,
                timeframe=timeframe,
                bot_token=BOT_TOKEN,
                chat_id=CHAT_ID,
                price_monitor=price_monitor,
                use_file_data=True
            )
            detectors.append(detector)
            print(f"✅ Создан детектор ФАЙЛ: {asset} {timeframe}")

    print(f"\n📊 Итого создано {len(detectors)} детекторов:")
    print(f"   - Криптовалюты: {len(crypto_assets)} активов × {len(crypto_timeframes)} таймфреймов = {len(crypto_assets) * len(crypto_timeframes)}")
    print(f"   - Файловые данные: {len(file_assets)} активов × {len(file_timeframes)} таймфреймов = {len(file_assets) * len(file_timeframes)}")
    print("🟢 Запуск ВСЕХ детекторов одновременно...")

    # Запускаем все задачи параллельно
    tasks = [detector.start_detection() for detector in detectors]

    # Добавляем мониторинг цен для файловых данных
    tasks.append(monitor_file_prices(price_monitor))

    # Запускаем все задачи
    await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n📢 Все сервисы остановлены")