import requests
import asyncio
from time_service import TimeService

class OrderBlockDetector:

    def __init__(self, timeframe, bot_token, chat_id):
        self.trading_pairs = ['BTCUSDT', 'ETHUSDT', 'IMOEXF', 'GLDRUBF']
        self.candles = {}  # Будет заполняться автоматически
        self.timeframe = timeframe
        self.time_service = TimeService()
        self.BOT_TOKEN = bot_token
        self.CHAT_ID = chat_id

        # Инициализируем словарь для каждой пары
        for pair in self.trading_pairs:
            self.candles[pair] = []

    def send_telegram_message(self, message_text):
        url = f"https://api.telegram.org/bot{self.BOT_TOKEN}/sendMessage"
        data = {'chat_id': self.CHAT_ID, 'text': message_text}

        try:
            response = requests.post(url, data=data)
            if response.status_code == 200:
                print("Сообщение отправлено!")
                return True
            else:
                print(f"Ошибка Telegram: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Ошибка подключения к Telegram: {e}")
            return False

    def get_price(self):
        """Получает цены ВСЕХ пар из разных источников"""
        current_prices = {}

        for pair in self.trading_pairs:
            try:
                if pair in ['BTCUSDT', 'ETHUSDT']:
                    # Binance цена
                    from binance.client import Client
                    client = Client()
                    price = float(client.get_symbol_ticker(symbol=pair)['price'])
                else:
                    # QUIK цена
                    from monitoring_quik import MQ
                    prices = MQ.read_prices()
                    price = prices.get(pair) if prices else None

                if price is not None:
                    current_prices[pair] = price
                else:
                    print(f"⚠️ Не удалось получить цену для {pair}")

            except Exception as e:
                print(f"❌ Ошибка получения цены для {pair}: {e}")

        return current_prices

    def analyze_all_pairs(self):
        """Анализирует ВЕСЬ словарь candles на наличие ордерблоков"""
        order_blocks = []  # список найденных ордерблоков

        for pair, candle_list in self.candles.items():
            # Должны быть РОВНО 2 свечи для анализа
            if len(candle_list) != 2:
                continue  # пропускаем если не 2 свечи

            # Всегда берем первую и вторую свечу (они всегда последние)
            first_candle = candle_list[0]  # более старая свеча
            second_candle = candle_list[1]  # более новая свеча

            prev_change = first_candle['change']
            curr_change = second_candle['change']

            has_trend_reversal = (prev_change * curr_change) < 0  # Смена направления
            has_strong_move = abs(curr_change) > abs(prev_change) * 2  # Сильное движение

            if has_trend_reversal and has_strong_move:
                if curr_change > 0:
                    block_type = 'GREEN'
                else:
                    block_type = 'RED'

                order_blocks.append(f"{pair}: {block_type}")
                print(f"✅ Найден ордерблок: {pair} {block_type}")

        # Отправляем одним сообщением если нашли ордерблоки
        if order_blocks:
            message = f"Таймфрейм → {self.timeframe}\n"
            message += "Найдены ордерблоки:\n"
            message += "\n".join(order_blocks)

            self.send_telegram_message(message)
            return True
        else:
            print(f"❌ На {self.timeframe} ордерблоки не обнаружены")
            return False

        # Отправляем сообщение если нашли ордерблоки
        if order_blocks_found:
            message = f"{self.timeframe}: Найдены ордерблоки:\n"
            for pair, block_type in order_blocks_found.items():
                message += f"{pair}: {block_type}\n"

            self.send_telegram_message(message)
            print(f"✅ Ордерблоки найдены: {order_blocks_found}")
            return order_blocks_found
        else:
            print(f"❌ Ордерблоки не обнаружены на {self.timeframe}")
            return {}


    async def start_detection(self):
        """Основной цикл для ВСЕХ пар на одном таймфрейме"""
        print(f"🚀 Запуск сервиса для таймфрейма {self.timeframe}")

        # Ждем первую свечу
        wait_time = await self.time_service.get_time_to_candle_close(self.timeframe)
        if wait_time > 1:
            formatted_time = await self.time_service.format_time_remaining(wait_time)
            print(f"⏰ Ожидание закрытия свечи {self.timeframe}: {formatted_time}")
            await asyncio.sleep(wait_time)

        # Стартовые цены (открытие свечи)
        start_prices = self.get_price()
        print(f"📊 Стартовые цены получены")

        while True:
            # Ждем закрытие свечи
            wait_time = await self.time_service.get_time_to_candle_close(self.timeframe)
            if wait_time > 1:
                formatted_time = await self.time_service.format_time_remaining(wait_time)
                print(f"⏰ Ожидание закрытия свечи {self.timeframe}: {formatted_time}")
                await asyncio.sleep(wait_time)

            # Цены закрытия
            current_prices = self.get_price()
            print(f"🎯 Цены закрытия получены")

            # Создаем/обновляем свечи для КАЖДОЙ пары
            for pair in self.trading_pairs:
                if pair in start_prices and pair in current_prices:
                    open_price = start_prices[pair]
                    close_price = current_prices[pair]

                    candle = {
                        "open": open_price,
                        "close": close_price,
                        "change": close_price - open_price
                    }

                    # Добавляем свечу в историю
                    self.candles[pair].append(candle)

                    # ВАЖНО: Храним только 2 последние свечи (скользящее окно)
                    if len(self.candles[pair]) > 2:
                        self.candles[pair] = self.candles[pair][-2:]  # оставляем только 2 последние

                    print(f"{pair}: {open_price:.2f} → {close_price:.2f} ({candle['change']:+.2f})")

            # Анализируем только если у ВСЕХ пар есть по 2 свечи
            all_pairs_ready = all(len(candle_list) == 2 for candle_list in self.candles.values())

            if all_pairs_ready:
                print(f"🔍 Анализ всех пар на {self.timeframe}...")
                self.analyze_all_pairs()
            else:
                print(f"Ожидаем накопления 2 свечей для всех пар...")

            # Обновляем стартовые цены для следующей свечи
            start_prices = current_prices.copy()
            print("Стартовые цены обновлены\n" + "="*50)

def main():
    # Пример использования
    detector = OrderBlockDetector(
        timeframe='5m',
        bot_token='8442684870:AAEwtD81q4QbQSL5D7fnGUYY7wiOkODAHGM',
        chat_id='1112634401'
    )
    asyncio.run(detector.start_detection())

if __name__ == "__main__":
    main()