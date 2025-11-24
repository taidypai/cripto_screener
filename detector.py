# detector.py
import requests
import asyncio
from time_service import TimeService
from datetime import datetime
from services.level_service import level_service  # Добавьте этот импорт

class Detector:

    def __init__(self, timeframe, bot_token, chat_id):
        self.trading_pairs = ['IMOEX', 'GLDRUBF', 'NASD']  # Обновите пары согласно клавиатуре
        self.candles = {}
        self.timeframe = timeframe
        self.time_service = TimeService()
        self.BOT_TOKEN = bot_token
        self.CHAT_ID = chat_id

        # Инициализируем свечи для каждой пары
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
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                print(f"[{self.timeframe}] ✅ Сообщение отправлено в Telegram!")
                return True
            else:
                print(f"[{self.timeframe}] ❌ Ошибка Telegram {response.status_code}: {response.text}")
                return False
        except Exception as e:
            print(f"[{self.timeframe}] ❌ Ошибка подключения к Telegram: {e}")
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
                    pass

            except Exception as e:
                pass

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

        # Обновляем закрытие (текущая цена)
        candle['close'] = current_price

    def check_liquidity_removal(self, pair):
        """Проверяет снятие ликвидности для пары"""
        candle = self.candles[pair]

        # Проверяем, что все значения инициализированы
        if any(v is None for v in [candle['open'], candle['high'], candle['low'], candle['close']]):
            return False

        # Вычисляем тело свечи
        body_size = abs(candle['close'] - candle['open'])

        # Вычисляем нижний фитиль
        if candle['close'] > candle['open']:  # Бычья свеча
            lower_wick = candle['open'] - candle['low']
        else:  # Медвежья свеча
            lower_wick = candle['close'] - candle['low']

        # Проверяем условие: нижний фитиль > тела свечи в 2 раза
        # И нижний фитиль должен быть положительным (> 0)
        if body_size > 0 and lower_wick > 0 and lower_wick > body_size * 2:
            return True

        return False

    def analyze_all_pairs(self):
        """Анализирует ВСЕ пары на снятие ликвидности в КОНЦЕ свечи с проверкой касания уровней"""
        valid_liquidity_removals = []

        for pair in self.trading_pairs:
            # Проверяем снятие ликвидности для текущей пары
            if self.check_liquidity_removal(pair):
                candle = self.candles[pair]

                # ПРОВЕРЯЕМ КАСАНИЕ УРОВНЕЙ - ключевое изменение!
                price_touches_level = level_service.check_price_touches_level(
                    pair,
                    candle['low'],
                    candle['high']
                )

                # Снятие ликвидности считается валидным только если цена коснулась уровня
                if price_touches_level:
                    # Определяем тип свечи (бычья/медвежья)
                    if candle['close'] > candle['open']:
                        candle_type = 'БЫЧЬЯ'
                    else:
                        candle_type = 'МЕДВЕЖЬЯ'

                    # Получаем активные уровни для этой пары
                    active_levels = level_service.get_active_levels_for_pair(pair)

                    # Находим уровень, которого коснулась цена
                    touched_levels = []
                    for level in active_levels:
                        if candle['low'] <= level <= candle['high']:
                            touched_levels.append(level)

                    message_info = f"{pair}: {candle_type}"
                    if touched_levels:
                        message_info += f" 🎯 Уровень: {', '.join(map(str, touched_levels))}"

                    # Добавляем в список валидных снятий ликвидности
                    valid_liquidity_removals.append(message_info)
                    print(f"[{self.timeframe}] 🎯 ВАЛИДНОЕ снятие ликвидности: {pair} с касанием уровня")

        # Отправляем сообщение если нашли ВАЛИДНЫЕ снятия ликвидности
        if valid_liquidity_removals:
            message = f"🎯 ВАЛИДНОЕ СНЯТИЕ ЛИКВИДНОСТИ ({self.timeframe})\n"
            message += "\n".join(valid_liquidity_removals)
            message += f"\n\n✅ Подтверждено касанием пользовательских уровней"

            self.send_telegram_message(message)
            return True

        return False

    def reset_candle(self, pair):
        """Сбрасывает свечу для нового периода"""
        self.candles[pair] = {
            'open': None,
            'high': None,
            'low': None,
            'close': None
        }

    async def start_detection(self):
        """Основной цикл для всех пар на указанном таймфрейме"""
        print(f"[{self.timeframe}] 🚀 Запуск сервиса обнаружения снятия ликвидности")

        while True:
            try:
                # Ждем начало новой свечи
                wait_time = await self.time_service.get_time_to_candle_close(self.timeframe)
                if wait_time > 0:
                    formatted_time = await self.time_service.format_time_remaining(wait_time)
                    print(f"[{self.timeframe}] ⏳ Ожидание начала новой свечи: {formatted_time}")
                    await asyncio.sleep(wait_time)

                # Получаем начальную цену (открытие новой свечи)
                start_prices = self.get_price()
                print(f"[{self.timeframe}] 📊 Новая свеча началась. Стартовые цены: {start_prices}")

                # Инициализируем свечи
                for pair in self.trading_pairs:
                    if pair in start_prices:
                        self.candles[pair]['open'] = start_prices[pair]
                        self.candles[pair]['high'] = start_prices[pair]
                        self.candles[pair]['low'] = start_prices[pair]
                        self.candles[pair]['close'] = start_prices[pair]

                # Основной цикл обновления в течение свечи
                candle_start_time = datetime.now()
                while True:
                    # Получаем текущие цены
                    current_prices = self.get_price()

                    # Обновляем свечи для каждой пары
                    for pair in self.trading_pairs:
                        if pair in current_prices:
                            self.update_candle(pair, current_prices[pair])

                    # Проверяем, не закончилась ли текущая свеча
                    time_remaining = await self.time_service.get_time_to_candle_close(self.timeframe)

                    # Если до конца свечи осталось меньше 1 секунды - завершаем свечу
                    if time_remaining <= 1:
                        print(f"[{self.timeframe}] 🔚 Свеча завершена. Анализируем...")

                        # Анализируем на снятие ликвидности в КОНЦЕ свечи с проверкой уровней
                        self.analyze_all_pairs()
                        await asyncio.sleep(1)
                        # Сбрасываем свечи для следующего периода
                        for pair in self.trading_pairs:
                            self.reset_candle(pair)

                        print(f"[{self.timeframe}] 🔄 Свечи сброшены. Следующая...")
                    else:
                        # Ждем 1 секунду перед следующим обновлением
                        await asyncio.sleep(1)

            except Exception as e:
                print(f"[{self.timeframe}] ❌ Ошибка в основном цикле: {e}")
                await asyncio.sleep(5)
