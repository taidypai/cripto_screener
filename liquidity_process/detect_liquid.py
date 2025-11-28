import requests
import asyncio
import os
import sys
from datetime import datetime


sys.path.append(r"C:\Users\Вадим\Documents\python\trade-brain-main")
import config
from components.time_service import TimeService
from components.send_telegram_message import send_tg_message
from components.get_price_action import get_price

class Detector_liquid:
    def __init__(self, timeframe):
        # Используем те же названия пар, что и в QUIK
        self.trading_pairs = ['IMOEXF', 'GLDRUBF']
        self.candles = {}
        self.timeframe = timeframe
        self.time_service = TimeService()

        # Создаем свечи для каждой пары
        for pair in self.trading_pairs:
            self.candles[pair] = {
                'open': None,
                'high': None,
                'low': None,
                'close': None
            }

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
            print(f"[{self.timeframe}] Обнаружено снятие ликвидности для {pair}")
            return True

        return False

    def analyze_all_pairs(self):
        for pair in self.trading_pairs:
            if self.check_liquidity_removal(pair): # Проверяем снятие ликвидности для текущей пары
                candle = self.candles[pair]
                message = f"{pair} [{self.timeframe}] "
                send_tg_message(message)
                print(f"[{self.timeframe}] снятие ликвидности: {pair}")
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
        while True:
            try:
                # Ждем начало новой свечи
                wait_time = await self.time_service.get_time_to_candle_close(self.timeframe)
                if wait_time > 0:
                    formatted_time = await self.time_service.format_time_remaining(wait_time)
                    await asyncio.sleep(wait_time)

                # Получаем начальную цену (открытие новой свечи)
                start_prices = get_price()
                print(f"✓ [{self.timeframe}] Новая свеча IMP Success")

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
                    current_prices = get_price()

                    # Обновляем свечи для каждой пары
                    for pair in self.trading_pairs:
                        if pair in current_prices:
                            self.update_candle(pair, current_prices[pair])

                    # Проверяем, не закончилась ли текущая свеча
                    time_remaining = await self.time_service.get_time_to_candle_close(self.timeframe)

                    # Если до конца свечи осталось меньше 1 секунды - завершаем свечу
                    if time_remaining == 1:
                        print(f"[{self.timeframe}] Свеча завершена. Анализ...")

                        self.analyze_all_pairs()

                        # Сбрасываем свечи для следующего периода
                        for pair in self.trading_pairs:
                            self.reset_candle(pair)

                        print(f"[{self.timeframe}] Свечи сброшены. Следующая...")
                        break
                    else:
                        # Ждем 1 секунду перед следующим обновлением
                        await asyncio.sleep(1)

            except Exception as e:
                print(f"[{self.timeframe}] Ошибка в основном цикле: {e}")
                await asyncio.sleep(5)


