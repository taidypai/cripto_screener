import requests
import asyncio
import json
import os
import sys
from datetime import datetime


sys.path.append(r"C:\Users\Вадим\Documents\python\trade-brain-main")
import config
from components.time_service import TimeService
from components.send_telegram_message import send_tg_message
from components.get_price_action import get_price

class Detector_impuls:
    def __init__(self, timeframe):
        # Используем те же названия пар, что и в QUIK
        self.trading_pairs = ['IMOEXF', 'GLDRUBF']
        self.candles = {}
        self.timeframe = timeframe
        self.time_service = TimeService()
        self.impuls_candels = []

        # Создаем свечи для каждой пары
        for pair in self.trading_pairs:
            self.candles[pair] = {
                'open': None,
                'high': None
            }

    def update_candle(self, pair, current_price):
        """Обновляет свечу новым значением цены"""
        candle = self.candles[pair]

        # Если это первое значение - инициализируем свечу
        if candle['open'] is None:
            candle['open'] = current_price
            candle['close'] = current_price
            return

        # Обновляем закрытие (текущая цена)
        candle['close'] = current_price

    def add_impuls_removal(self, pair):
        """Проверяет импульс для пары"""
        candle = self.candles[pair]

        # Проверяем, что все значения инициализированы
        if any(v is None for v in [candle['open'], candle['high']]):
            return False

        # Вычисляем тело свечи
        if abs(candle['close'] - candle['open']) < 0:
            self.impuls_candels.append(1)
        else:
            self.impuls_candels.append(0)
        return True

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
                print(f"✓ [{self.timeframe}] Новая свеча LIQ  Success")

                # Инициализируем свечи
                for pair in self.trading_pairs:
                    if pair in start_prices:
                        self.candles[pair]['open'] = start_prices[pair]
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
                    if time_remaining == 1:
                        if self.add_impuls_removal(pair):
                            print(f"[{self.timeframe}] Свеча завершена. Анализ...")
                            if len(self.impuls_candels)==4 and sum(impuls_down) >= 3:
                                message = f"Резкий импульс {pair} [{self.timeframe}]"
                                send_tg_message(message)
                                self.impuls_candels = self.impuls_candels[1:]
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