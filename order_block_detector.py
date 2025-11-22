import requests
import asyncio
from time_service import TimeService

class Detector:

    def __init__(self, timeframe, bot_token, chat_id):
        self.trading_pairs = ['IMOEXF', 'GLDRUBF']
        self.candles = {}  # Будет заполняться автоматически
        self.timeframe = timeframe
        self.time_service = TimeService()
        self.BOT_TOKEN = bot_token
        self.CHAT_ID = chat_id

        # Инициализируем словарь для каждой пары
        for pair in self.trading_pairs:
            self.candles[pair] = {
                'open': None,
                'high': None,
                'low': None,
                'close': None
            }

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
        current_prices = {}

        for pair in self.trading_pairs:
            try:
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

    def update_candle(self, pair, current_price):
        """Обновляет свечу новым значением цены"""
        candle = self.candles[pair]

        # Если это первое значение - инициализируем свечу
        if candle['open'] is None:
            candle['open'] = current_price
            candle['high'] = current_price
            candle['low'] = current_price
            candle['close'] = current_price
            return

        # Обновляем максимум и минимум
        if current_price > candle['high']:
            candle['high'] = current_price
        if current_price < candle['low']:
            candle['low'] = current_price

        # Обновляем закрытие
        candle['close'] = current_price

    def check_liquidity_removal(self, pair):
        """Проверяет снятие ликвидности для пары"""
        candle = self.candles[pair]

        # Проверяем, что все значения инициализированы
        if any(v is None for v in [candle['open'], candle['high'], candle['low'], candle['close']]):
            return False

        # Вычисляем тело свечи
        body_size = abs(candle['close'] - candle['open'])

        # Вычисляем верхний и нижний тени (фитили)
        if candle['close'] > candle['open']:  # Бычья свеча
            upper_wick = candle['high'] - candle['close']
            lower_wick = candle['open'] - candle['low']
        else:  # Медвежья свеча
            upper_wick = candle['high'] - candle['open']
            lower_wick = candle['close'] - candle['low']

        # Проверяем условие снятия ликвидности: тело свечи < нижнего фитиля в 2 раза
        if body_size > 0 and lower_wick > body_size * 2:
            return True

        return False

    def analyze_all_pairs(self):
        """Анализирует ВСЕ пары на снятие ликвидности"""
        liquidity_removals = []  # список найденных снятий ликвидности

        for pair in self.trading_pairs:
            if self.check_liquidity_removal(pair):
                candle = self.candles[pair]

                # Определяем тип свечи
                if candle['close'] > candle['open']:
                    candle_type = 'БЫЧЬЯ'
                else:
                    candle_type = 'МЕДВЕЖЬЯ'

                # Вычисляем параметры для сообщения
                body_size = abs(candle['close'] - candle['open'])
                lower_wick = candle['open'] - candle['low'] if candle['close'] > candle['open'] else candle['close'] - candle['low']

                message_info = f"{pair}: {candle_type} | Тело: {body_size:.2f} | Нижняя тень: {lower_wick:.2f}"
                liquidity_removals.append(message_info)
                print(f"✅ Найдено снятие ликвидности: {pair}")

        # Отправляем одним сообщением если нашли снятия ликвидности
        if liquidity_removals:
            message = f"Таймфрейм → {self.timeframe}\n"
            message += "Обнаружено снятие ликвидности:\n"
            message += "\n".join(liquidity_removals)

            self.send_telegram_message(message)
            return True
        else:
            print(f"❌ На {self.timeframe} снятие ликвидности не обнаружено")
            return False

    async def start_detection(self):
        """Основной цикл для ВСЕХ пар"""
        print(f"🚀 Запуск сервиса для таймфрейма {self.timeframe}")

        while True:
            # Получаем текущие цены каждую секунду
            current_prices = self.get_price()

            # Обновляем свечи для каждой пары
            for pair in self.trading_pairs:
                if pair in current_prices:
                    self.update_candle(pair, current_prices[pair])
                    print(f"{pair}: O:{self.candles[pair]['open']:.2f} H:{self.candles[pair]['high']:.2f} L:{self.candles[pair]['low']:.2f} C:{self.candles[pair]['close']:.2f}")

            # Анализируем на снятие ликвидности
            print(f"🔍 Анализ всех пар на {self.timeframe}...")
            self.analyze_all_pairs()

            # Ждем 1 секунду перед следующим обновлением
            await asyncio.sleep(1)

def main():
    # Пример использования
    detector = Detector(
        timeframe='1s',
        bot_token='8442684870:AAEwtD81q4QbQSL5D7fnGUYY7wiOkODAHGM',
        chat_id='1112634401'
    )
    asyncio.run(detector.start_detection())

if __name__ == "__main__":
    main()
