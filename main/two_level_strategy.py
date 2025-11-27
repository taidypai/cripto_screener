# two_level_strategy.py
import time
import re
import os
import asyncio
from datetime import datetime

class TwoLevelStrategy:
    def __init__(self):
        self.executive_file = "C:/QUIK_DATA/executive.txt"
        self.instruments = {
            'GLDRUBF': {'step': 0.1, 'step_cost': 0.1, 'lot_price': 2664.45},
            'IMOEXF': {'step': 0.5, 'step_cost': 5, 'lot_price': 6794.2}
        }
        self.active_trades = {}  # Храним активные сделки
        self.pending_levels = {}  # Ожидающие уровни для входа
        self.setup_environment()

    def setup_environment(self):
        """Создает директорию и файл если не существуют"""
        directory = os.path.dirname(self.executive_file)
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✓ Создана директория: {directory}")

    def read_executive_file(self):
        """Чтение всего executive файла"""
        try:
            with open(self.executive_file, 'r') as f:
                return f.read()
        except Exception as e:
            print(f"Ошибка чтения executive файла: {e}")
            return ""
    def load_user_levels(self):
        """Загрузка уровней из файла"""
        try:
            if os.path.exists(self.levels_file):
                with open(self.levels_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Ошибка загрузки уровней: {e}")
            return {}

    def get_active_levels_for_pair(self, pair):
        """Получение активных уровней для конкретной пары"""
        try:
            user_levels = self.load_user_levels()
            active_levels = []
            current_time = datetime.now()

            for user_id, user_data in user_levels.items():
                if pair in user_data:
                    for level in user_data[pair]:
                        try:
                            expires_at = datetime.fromisoformat(level["expires_at"])
                            if expires_at > current_time:
                                active_levels.append({
                                    'price': level["price"],
                                    'stop_loss': level["stop_loss"]
                                })
                        except Exception as e:
                            print(f"Ошибка парсинга времени уровня: {e}")
                            continue

            return active_levels

        except Exception as e:
            print(f"Ошибка получения уровней для {pair}: {e}")
            return []

    def read_section(self, content, section_name):
        """Чтение секции из файла"""
        match = re.search(r'\[' + section_name + r'\](.*?)(?=\[|$)', content, re.DOTALL)
        return match.group(1).strip() if match else None

    def parse_section(self, content):
        """Парсинг секции в словарь"""
        lines = content.split('\n')
        data = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                data[key.strip()] = value.strip()
        return data

    def get_current_prices(self):
        """Получение текущих цен из строки PRICES в executive.txt"""
        prices = {}
        try:
            content = self.read_executive_file()

            # Ищем строку PRICES:
            for line in content.split('\n'):
                if line.startswith('PRICES:'):
                    # Формат: PRICES:GLDRUBF/цена; IMOEXF/цена
                    prices_data = line.replace('PRICES:', '').strip()

                    # Разделяем по точкам с запятой
                    pairs = prices_data.split(';')

                    for pair_data in pairs:
                        pair_data = pair_data.strip()
                        if '/' in pair_data:
                            symbol, price_str = pair_data.split('/', 1)
                            symbol = symbol.strip()
                            price_str = price_str.strip()

                            try:
                                prices[symbol] = float(price_str)
                            except ValueError:
                                print(f"❌ Ошибка преобразования цены: {symbol} = {price_str}")
                                continue

                    break  # Нашли строку PRICES, выходим

            return prices

        except Exception as e:
            print(f"❌ Ошибка получения цен из PRICES: {e}")
            return {}

    def get_balance_data(self):
        """Получение данных баланса из executive.txt"""
        try:
            content = self.read_executive_file()
            balance_content = self.read_section(content, 'BALANCE')
            if balance_content:
                return self.parse_section(balance_content)
            return None
        except Exception as e:
            print(f"❌ Ошибка получения баланса: {e}")
            return None

    def calculate_position_size(self, balance, pair, stop_loss, market_price):
        """Расчет объема позиции с риском 1% от депозита"""
        instrument = self.instruments[pair]

        # Расчет риска на сделку (1% от депозита)
        risk_amount = float(balance['available']) * 0.01

        # Расчет количества лотов
        price_diff = abs(float(market_price) - stop_loss)
        steps = price_diff / instrument['step']
        risk_per_step = steps * instrument['step_cost']

        lots = int(risk_amount / risk_per_step) if risk_per_step > 0 else 0

        # Минимальная проверка
        if lots < 1:
            lots = 1

        return lots

    def calculate_take_profit(self, market_price, stop_loss, rr_ratio=2.0):
        """Расчет тейк-профита по RR ratio"""
        if float(market_price) > stop_loss:  # BUY
            take_profit = float(market_price) + (float(market_price) - stop_loss) * rr_ratio
        else:  # SELL
            take_profit = float(market_price) - (stop_loss - float(market_price)) * rr_ratio

        return round(take_profit, 2)

    def process_level_signal(self, level_signal):
        """Обработка LEVEL сигнала - добавление в ожидание"""
        pair = level_signal['pair']
        level_price = float(level_signal['price'])
        stop_loss = float(level_signal['stop_loss'])

        # Проверяем, нет ли уже активной сделки или ожидания для этой пары
        if self.has_active_trade_or_level(pair):
            print(f"❌ Для {pair} уже есть активная сделка или ожидание уровня")
            return False

        # Сохраняем уровень для мониторинга
        level_id = f"level_{pair}_{int(time.time())}"
        self.pending_levels[level_id] = {
            'pair': pair,
            'level_price': level_price,
            'stop_loss': stop_loss,
            'status': 'pending',
            'created_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        print(f"✅ Добавлен уровень для мониторинга: {pair} на цене {level_price}, SL: {stop_loss}")
        return True

    def process_telega_signal(self, trade_signal):
        """Обработка TELEGA сигнала и создание сделки 1 уровня"""
        pair = trade_signal['pair']
        stop_loss = float(trade_signal['stop_loss'])

        # Проверяем, нет ли уже активной сделки для этой пары
        if self.has_active_trade(pair):
            print(f"❌ Для {pair} уже есть активная сделка")
            return False

        # Получаем баланс
        balance_data = self.get_balance_data()
        if not balance_data:
            print("❌ Не удалось получить баланс")
            return False

        # Получаем текущую цену из PRICES
        market_price = self.get_current_prices().get(pair)
        if not market_price:
            print(f"❌ Не удалось получить цену для {pair} из PRICES")
            return False

        # Расчет параметров сделки 1 уровня
        lots = self.calculate_position_size(balance_data, pair, stop_loss, market_price)
        take_profit = self.calculate_take_profit(market_price, stop_loss, 2.0)

        # Определение направления сделки
        operation = 'B' if market_price > stop_loss else 'S'

        # Сохраняем данные сделки
        trade_id = f"{pair}_{int(time.time())}"
        self.active_trades[trade_id] = {
            'pair': pair,
            'entry_price': market_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'total_lots': lots,
            'remaining_lots': lots,
            'operation': operation,
            'level': 1,
            'status': 'active',
            'open_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Добавляем команду на открытие позиции
        self.add_deal_command(pair, operation, lots)

        print(f"✅ Создана сделка 1 уровня: {pair} {operation} {lots} лотов")
        print(f"   Вход: {market_price}, SL: {stop_loss}, TP: {take_profit}")

        return True

    def has_active_trade(self, pair):
        """Проверяет, есть ли активная сделка для пары"""
        for trade_id, trade in self.active_trades.items():
            if trade['pair'] == pair and trade['status'] == 'active':
                return True
        return False

    def has_active_trade_or_level(self, pair):
        """Проверяет, есть ли активная сделка или ожидание уровня для пары"""
        # Проверяем активные сделки
        if self.has_active_trade(pair):
            return True

        # Проверяем ожидающие уровни
        for level_id, level in self.pending_levels.items():
            if level['pair'] == pair and level['status'] == 'pending':
                return True

        return False

    def add_deal_command(self, pair, operation, quantity):
        """Добавляет команду DEAL в файл"""
        try:
            with open(self.executive_file, 'a') as f:
                f.write(f"DEAL:{pair}/{operation}/{quantity}\n")
            print(f"✅ Добавлена команда: DEAL:{pair}/{operation}/{quantity}")
        except Exception as e:
            print(f"❌ Ошибка добавления команды DEAL: {e}")

    def check_pending_levels(self):
        """Проверка достижения ожидающих уровней"""
        current_prices = self.get_current_prices()

        for level_id, level in list(self.pending_levels.items()):
            if level['status'] != 'pending':
                continue

            current_price = current_prices.get(level['pair'])
            if not current_price:
                continue

            # Проверяем достижение уровня (цена коснулась уровня)
            level_price = level['level_price']
            tolerance = level_price * 0.001  # Допуск 0.1%

            if abs(current_price - level_price) <= tolerance:
                print(f"🎯 Уровень достигнут: {level['pair']} на цене {level_price}")

                # Создаем TELEGA сигнал из уровня
                trade_signal = {
                    'pair': level['pair'],
                    'stop_loss': level['stop_loss']
                }

                if self.process_telega_signal(trade_signal):
                    # Уровень активирован, удаляем его из ожидания
                    level['status'] = 'activated'
                    self.remove_level_line(level['pair'], level_price)
                else:
                    # Ошибка активации, оставляем уровень
                    print(f"❌ Ошибка активации сделки для уровня {level_id}")

    def check_price_levels(self):
        """Проверка достижения ценовых уровней для активных сделок"""
        current_prices = self.get_current_prices()

        for trade_id, trade in list(self.active_trades.items()):
            if trade['status'] != 'active':
                continue

            current_price = current_prices.get(trade['pair'])
            if not current_price:
                continue

            # Проверяем достижение стоп-лосса
            if self.is_stop_loss_hit(trade, current_price):
                print(f"🔴 СТОП-ЛОСС: {trade['pair']} на уровне {trade['level']}")
                self.close_trade(trade_id, 'stop_loss')
                continue

            # Проверяем достижение тейк-профита
            if self.is_take_profit_hit(trade, current_price):
                print(f"🟢 ТЕЙК-ПРОФИТ: {trade['pair']} на уровне {trade['level']}")
                self.handle_take_profit(trade_id, current_price)
                continue

    def is_stop_loss_hit(self, trade, current_price):
        """Проверяет срабатывание стоп-лосса"""
        if trade['operation'] == 'B':  # BUY позиция
            return current_price <= trade['stop_loss']
        else:  # SELL позиция
            return current_price >= trade['stop_loss']

    def is_take_profit_hit(self, trade, current_price):
        """Проверяет срабатывание тейк-профита"""
        if trade['operation'] == 'B':  # BUY позиция
            return current_price >= trade['take_profit']
        else:  # SELL позиция
            return current_price <= trade['take_profit']

    def handle_take_profit(self, trade_id, current_price):
        """Обработка срабатывания тейк-профита"""
        trade = self.active_trades[trade_id]

        if trade['level'] == 1:
            # Первый уровень - закрываем половину позиции
            lots_to_close = trade['remaining_lots'] // 2
            if lots_to_close < 1:  # Минимум 1 лот
                lots_to_close = 1

            # Закрываем часть позиции
            close_operation = 'S' if trade['operation'] == 'B' else 'B'
            self.add_deal_command(trade['pair'], close_operation, lots_to_close)

            # Обновляем оставшиеся лоты
            trade['remaining_lots'] -= lots_to_close

            if trade['remaining_lots'] > 0:
                # Переходим на второй уровень
                self.upgrade_to_level_2(trade_id, current_price)
            else:
                # Полностью закрыли сделку
                self.close_trade(trade_id, 'take_profit')

        elif trade['level'] == 2:
            # Второй уровень - полностью закрываем сделку
            self.close_trade(trade_id, 'take_profit')

    def upgrade_to_level_2(self, trade_id, current_price):
        """Переход на второй уровень стратегии"""
        trade = self.active_trades[trade_id]

        # Новый стоп-лосс на уровне безубытка + несколько пунктов
        if trade['operation'] == 'B':
            new_stop_loss = trade['entry_price'] + 2  # +2 пункта для безубытка
        else:
            new_stop_loss = trade['entry_price'] - 2  # -2 пункта для безубытка

        # Новый тейк-профит с RR 2.0 от оставшейся позиции
        new_take_profit = self.calculate_take_profit(current_price, new_stop_loss, 2.0)

        # Обновляем параметры сделки
        trade['stop_loss'] = new_stop_loss
        trade['take_profit'] = new_take_profit
        trade['level'] = 2

        print(f"🔄 Переход на уровень 2: {trade['pair']}")
        print(f"   Новый SL: {new_stop_loss}, Новый TP: {new_take_profit}")

    def close_trade(self, trade_id, reason):
        """Полное закрытие сделки"""
        trade = self.active_trades[trade_id]

        if trade['remaining_lots'] > 0:
            # Закрываем оставшиеся лоты
            close_operation = 'S' if trade['operation'] == 'B' else 'B'
            self.add_deal_command(trade['pair'], close_operation, trade['remaining_lots'])

        trade['status'] = 'closed'
        trade['close_reason'] = reason
        trade['close_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        print(f"🔒 Сделка закрыта: {trade['pair']} - {reason}")

    def remove_telega_line(self, line_to_remove):
        """Удаляет обработанную строку TELEGA из файла"""
        self.remove_line_from_file(line_to_remove, "TELEGA")

    def remove_level_line(self, pair, level_price):
        """Удаляет обработанную строку LEVEL из файла"""
        line_to_remove = f"LEVEL:{pair}/{level_price}"
        self.remove_line_from_file(line_to_remove, "LEVEL")

    def remove_line_from_file(self, line_to_remove, line_type):
        """Удаляет строку из файла"""
        try:
            with open(self.executive_file, 'r') as f:
                lines = f.readlines()

            with open(self.executive_file, 'w') as f:
                removed = False
                for line in lines:
                    if line.strip() == line_to_remove.strip() and not removed:
                        # Пропускаем первую найденную строку
                        removed = True
                        continue
                    f.write(line)

            if removed:
                print(f"✅ Удалена строка {line_type}: {line_to_remove.strip()}")
            else:
                print(f"⚠️ Строка {line_type} не найдена: {line_to_remove.strip()}")

        except Exception as e:
            print(f"❌ Ошибка удаления строки {line_type}: {e}")

    def monitor_and_process(self):
        """Основной цикл мониторинга"""
        print("🚀 Запуск двухуровневой стратегии...")

        while True:
            try:
                content = self.read_executive_file()

                # Проверяем LEVEL сигналы (лимитные ордера)
                if 'LEVEL:' in content:
                    lines = content.split('\n')
                    for line in lines:
                        if line.startswith('LEVEL:'):
                            # Формат: LEVEL:pair/price/stop_loss
                            parts = line.replace('LEVEL:', '').strip().split('/')
                            if len(parts) >= 3:
                                pair = parts[0].strip()
                                price = float(parts[1].strip())
                                stop_loss = float(parts[2].strip())

                                # Обрабатываем LEVEL сигнал
                                level_signal = {'pair': pair, 'price': price, 'stop_loss': stop_loss}
                                if self.process_level_signal(level_signal):
                                    # Уровень добавлен в мониторинг
                                    pass

                # Проверяем TELEGA сигналы (моментальные сделки)
                if 'TELEGA:' in content:
                    lines = content.split('\n')
                    for line in lines:
                        if line.startswith('TELEGA:'):
                            # Формат: TELEGA:pair:stop_loss
                            parts = line.split(':')
                            if len(parts) >= 3:
                                pair = parts[1].strip()
                                stop_loss = float(parts[2].strip())

                                # Обрабатываем сигнал
                                trade_signal = {'pair': pair, 'stop_loss': stop_loss}
                                if self.process_telega_signal(trade_signal):
                                    # Удаляем обработанную строку TELEGA
                                    self.remove_telega_line(line)

                # Проверяем ожидающие уровни
                self.check_pending_levels()

                # Проверяем ценовые уровни активных сделок
                self.check_price_levels()

                time.sleep(1)  # Проверяем каждую секунду

            except Exception as e:
                print(f"❌ Ошибка в основном цикле: {e}")
                time.sleep(5)

if __name__ == "__main__":
    strategy = TwoLevelStrategy()
    strategy.monitor_and_process()