import requests
import asyncio
import json
import os
from datetime import datetime
from time_service import TimeService

class Detector:

    def __init__(self, timeframe, bot_token, chat_id):
        # Используем те же названия пар, что и в QUIK
        self.trading_pairs = ['IMOEXF', 'GLDRUBF']
        self.candles = {}
        self.timeframe = timeframe
        self.time_service = TimeService()
        self.BOT_TOKEN = bot_token
        self.CHAT_ID = chat_id
        self.levels_file = "user_levels.json"

        # Инициализируем свечи для каждой пары
        for pair in self.trading_pairs:
            self.candles[pair] = {
                'open': None,
                'high': None,
                'low': None,
                'close': None
            }

    def load_user_levels(self):
        """Загрузка уровней из файла user_levels.json"""
        try:
            if os.path.exists(self.levels_file):
                with open(self.levels_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"❌ Ошибка загрузки уровней: {e}")
            return {}

    def get_active_levels_for_pair(self, pair):
        """Получение активных уровней для конкретной пары из файла"""
        try:
            user_levels = self.load_user_levels()
            active_levels = []
            current_time = datetime.now()

            # Преобразуем название пары для поиска в user_levels.json
            # IMOEXF -> IMOEX, GLDRUBF -> GLDRUBF (оставляем как есть)
            search_pair = pair.replace('F', '') if pair.endswith('F') else pair

            for user_id, user_data in user_levels.items():
                if search_pair in user_data:
                    for level in user_data[search_pair]:
                        try:
                            # Проверяем время истечения уровня
                            expires_at = datetime.fromisoformat(level["expires_at"])
                            if expires_at > current_time:
                                active_levels.append(level["price"])
                        except Exception as e:
                            print(f"❌ Ошибка парсинга времени уровня: {e}")
                            continue

            # Убираем дубликаты и сортируем
            active_levels = sorted(list(set(active_levels)))
            print(f"✅ Найдено {len(active_levels)} активных уровней для {pair}: {active_levels}")
            return active_levels

        except Exception as e:
            print(f"❌ Ошибка получения уровней для {pair}: {e}")
            return []

    def check_price_touches_level(self, pair, low_price, high_price, tolerance_percent=0.1):
        """Проверяет, коснулась ли цена какого-либо уровня в диапазоне low-high"""
        try:
            active_levels = self.get_active_levels_for_pair(pair)
            touched_levels = []

            for level in active_levels:
                # Проверяем, находится ли уровень в диапазоне low-high свечи
                if low_price <= level <= high_price:
                    print(f"✅ Price touched level {level} for {pair} (range: {low_price}-{high_price})")
                    touched_levels.append(level)

                # Проверяем касание с допуском (если цена почти дошла до уровня)
                else:
                    tolerance = level * tolerance_percent / 100
                    if abs(low_price - level) <= tolerance or abs(high_price - level) <= tolerance:
                        print(f"✅ Price nearly touched level {level} for {pair} (within {tolerance_percent}% tolerance)")
                        touched_levels.append(level)

            return touched_levels

        except Exception as e:
            print(f"❌ Error checking price touches level for {pair}: {e}")
            return []

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

            except Exception as e:
                print(f"[{self.timeframe}] ❌ Ошибка получения цены для {pair}: {e}")

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
            print(f"[{self.timeframe}] 🎯 Обнаружено снятие ликвидности для {pair}")
            print(f"    Открытие: {candle['open']}, Закрытие: {candle['close']}")
            print(f"    High: {candle['high']}, Low: {candle['low']}")
            print(f"    Тело свечи: {body_size}, Нижний фитиль: {lower_wick}")
            return True

        return False

    def analyze_all_pairs(self):
        """Анализирует ВСЕ пары на снятие ликвидности в КОНЦЕ свечи"""
        all_liquidity_removals = []
        priority_liquidity_removals = []

        for pair in self.trading_pairs:
            # Проверяем снятие ликвидности для текущей пары
            if self.check_liquidity_removal(pair):
                candle = self.candles[pair]

                # Определяем тип свечи (бычья/медвежья)
                if candle['close'] > candle['open']:
                    candle_type = 'БЫЧЬЯ'
                else:
                    candle_type = 'МЕДВЕЖЬЯ'

                # ПРОВЕРЯЕМ КАСАНИЕ УРОВНЕЙ из файла user_levels.json
                touched_levels = self.check_price_touches_level(
                    pair,
                    candle['low'],
                    candle['high']
                )

                message_info = f"{pair}: {candle_type}"

                # Если есть касание уровней - добавляем в приоритетный список
                if touched_levels:
                    message_info += f" 🎯 УРОВЕНЬ: {', '.join(map(str, touched_levels))}"
                    priority_liquidity_removals.append(message_info)
                    print(f"[{self.timeframe}] 🚨 ПРИОРИТЕТНОЕ снятие ликвидности: {pair} с касанием уровня")
                else:
                    # Обычное снятие ликвидности без касания уровня
                    all_liquidity_removals.append(message_info)
                    print(f"[{self.timeframe}] 📢 Обычное снятие ликвидности: {pair}")

        # Сначала отправляем ПРИОРИТЕТНЫЕ снятия (с касанием уровней)
        if priority_liquidity_removals:
            message = f"🚨 ПРИОРИТЕТНОЕ СНЯТИЕ ЛИКВИДНОСТИ ({self.timeframe})\n"
            message += "\n".join(priority_liquidity_removals)
            message += f"\n\n✅ Подтверждено касанием пользовательских уровней"

            self.send_telegram_message(message)

        # Затем отправляем ОБЫЧНЫЕ снятия (без касания уровней)
        if all_liquidity_removals:
            message = f"📢 СНЯТИЕ ЛИКВИДНОСТИ ({self.timeframe})\n"
            message += "\n".join(all_liquidity_removals)
            message += f"\n\n⚠️ Без касания пользовательских уровней"

            self.send_telegram_message(message)

        # Возвращаем True если были любые снятия ликвидности
        return len(priority_liquidity_removals) > 0 or len(all_liquidity_removals) > 0

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
                        print(f"[{self.timeframe}] 🔚 Свеча завершена. Финальный анализ...")

                        # Финальный анализ в конце свечи
                        self.analyze_all_pairs()

                        # Сбрасываем свечи для следующего периода
                        for pair in self.trading_pairs:
                            self.reset_candle(pair)

                        print(f"[{self.timeframe}] 🔄 Свечи сброшены. Следующая...")
                        break
                    else:
                        # Ждем 1 секунду перед следующим обновлением
                        await asyncio.sleep(1)

            except Exception as e:
                print(f"[{self.timeframe}] ❌ Ошибка в основном цикле: {e}")
                await asyncio.sleep(5)
