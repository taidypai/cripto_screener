import asyncio
import logging
import pytz
import datetime
import aiohttp
import requests
from binance.client import Client

logger = logging.getLogger(__name__)

class TimeService:
    def __init__(self):
        self.timeframe_minutes = {
            '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '4h': 240, '1d': 1440
        }
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
                        local_time = datetime.datetime.now().timestamp()
                        self.binance_server_time_diff = binance_server_time - local_time
                        self.last_sync_time = local_time
                        logger.info(f"Synced with Binance time. Diff: {self.binance_server_time_diff:.2f}s")
        except Exception as e:
            logger.error(f"Error syncing with Binance: {e}")

    def get_binance_time(self):
        local_time = datetime.datetime.now().timestamp()
        if local_time - self.last_sync_time > 3600:
            asyncio.create_task(self.sync_binance_time())

        binance_timestamp = local_time + self.binance_server_time_diff
        return datetime.datetime.fromtimestamp(binance_timestamp, pytz.UTC)

    async def get_time_to_candle_close(self, timeframe):
        now = self.get_binance_time()

        if timeframe not in self.timeframe_minutes:
            return 0

        minutes = self.timeframe_minutes[timeframe]
        current_minute = now.minute
        remainder = current_minute % minutes
        minutes_remaining = minutes - remainder

        close_time = now.replace(second=0, microsecond=0) + datetime.timedelta(minutes=minutes_remaining)
        seconds_remaining = max(0, int((close_time - now).total_seconds()))

        logger.info(f"Таймфрейм {timeframe}: текущее время {now.strftime('%H:%M:%S')}, "
                   f"закрытие в {close_time.strftime('%H:%M:%S')}, "
                   f"осталось {seconds_remaining} сек")

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

class OrderBlockDetector:
    def __init__(self, trading_pair, timeframe):
        self.trading_pair = trading_pair
        self.timeframe = timeframe
        self.client = Client()
        self.time_service = TimeService()
        self.BOT_TOKEN = "8442684870:AAEwtD81q4QbQSL5D7fnGUYY7wiOkODAHGM"
        self.CHAT_ID = "1112634401"

    def send_telegram_message(self, message_text):
        url = f"https://api.telegram.org/bot{self.BOT_TOKEN}/sendMessage"
        data = {'chat_id': self.CHAT_ID, 'text': message_text}

        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                print("✅ Сообщение отправлено!")
                return True
            else:
                print(f"❌ Ошибка: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False

    def analyze_candle_pattern(self, candle_history):
        if (candle_history[0].get("change") * candle_history[1].get("change") < 0) and (
            abs(candle_history[1].get("change")) / abs(candle_history[0].get("change")) > 2
        ):
            return "GREEN" if candle_history[1].get("change") > 0 else "RED"
        return False

    async def start_detection(self):
        candle_history = []
        VALID_PAIRS = ['BTCUSDT', 'ETHUSDT']

        if self.trading_pair not in VALID_PAIRS:
            print(f'Торговая пара {self.trading_pair} не валидна')
            return False

        print(f"🚀 Запуск сервиса {self.trading_pair} {self.timeframe}")
        await self.time_service.sync_binance_time()

        try:
            while True:
                wait_time = await self.time_service.get_time_to_candle_close(self.timeframe)

                if wait_time > 1:
                    formatted_time = await self.time_service.format_time_remaining(wait_time)
                    print(f"⏰ {self.trading_pair} {self.timeframe}: ждем {formatted_time} до закрытия свечи")
                    await asyncio.sleep(wait_time)
                else:
                    await asyncio.sleep(1)
                    continue

                try:
                    klines = self.client.get_klines(
                        symbol=self.trading_pair,
                        interval=self.timeframe,
                        limit=2
                    )

                    if len(klines) >= 2:
                        last_candle = klines[-2]
                        candle = {
                            "open": float(last_candle[1]),
                            "close": float(last_candle[4]),
                            "change": float(last_candle[4]) - float(last_candle[1]),
                        }
                    else:
                        current_price = float(self.client.get_symbol_ticker(symbol=self.trading_pair)['price'])
                        candle = {
                            "open": current_price,
                            "close": current_price,
                            "change": 0,
                        }

                except Exception as e:
                    logger.error(f"Ошибка получения данных для {self.trading_pair} {self.timeframe}: {e}")
                    continue

                logger.info(f"{self.trading_pair} {self.timeframe} - Получена свеча: {candle}")
                candle_history.append(candle)

                if len(candle_history) >= 2:
                    order_block_status = self.analyze_candle_pattern(candle_history[-2:])

                    if order_block_status:
                        message = f"{order_block_status} ОРДЕРБЛОК НАЙДЕН\n{self.trading_pair} {self.timeframe}: {order_block_status}"
                        self.send_telegram_message(message)
                        print(f"✅ {self.trading_pair} {self.timeframe}: ОРДЕРБЛОК НАЙДЕН - {order_block_status}")
                    else:
                        # УБРАН ВТОРОЙ ВЫЗОВ send_telegram_message - сообщение отправляется только один раз
                        print(f"❌ {self.trading_pair} {self.timeframe}: Ордерблок не найден")

                    if len(candle_history) > 2:
                        candle_history = candle_history[-2:]
                else:
                    print(f"⏳ {self.trading_pair} {self.timeframe}: Накопление истории ({len(candle_history)}/2)")

        except KeyboardInterrupt:
            print(f"\nСервис {self.trading_pair} {self.timeframe} остановлен")
        except Exception as e:
            print(f"Критическая ошибка в сервисе {self.trading_pair} {self.timeframe}: {e}")

async def main():
    print("🚀 Запуск детектора ордерблоков...")

    detectors = [
        OrderBlockDetector("BTCUSDT", "5m"),
        OrderBlockDetector("BTCUSDT", "15m"),
        OrderBlockDetector("BTCUSDT", "1h"),
        OrderBlockDetector("BTCUSDT", "4h"),
        OrderBlockDetector("BTCUSDT", "1d"),
        OrderBlockDetector("ETHUSDT", "5m"),
        OrderBlockDetector("ETHUSDT", "15m"),
        OrderBlockDetector("ETHUSDT", "1h"),
        OrderBlockDetector("ETHUSDT", "4h"),
        OrderBlockDetector("ETHUSDT", "1d")
    ]

    await asyncio.gather(
        *(detector.start_detection() for detector in detectors),
        return_exceptions=True
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n📢 Все сервисы остановлены")