import asyncio
import sys

sys.path.append(r"C:\Users\Вадим\Documents\python\trade-brain-main")
from components.finam_balance import balance_main
from components.send_telegram_message import send_tg_message
from components.get_price_action import get_price


class Louncher_trade_engine:
    def __init__(self, pair, stop_loss):
        PERCENT_RISK = 0.02
        self.INSTRUMENTS = {
            'GLDRUBF': {'step': 0.1, 'step_cost': 0.1, 'lot_price': 2664.45},
            'IMOEXF': {'step': 0.5, 'step_cost': 5, 'lot_price': 6794.2}
        }
        self.take_rr2 = 2
        self.pair = pair
        self.start_price = float(get_price()[pair])
        self.stop_loss = float(stop_loss)
        self.balance = float(balance_main())
        MAX_LOTS = self.balance // INSTRUMENTS[pair]['lot_price']
        self.QUANTITY = (self.balance * PERCENT_RISK) // (((self.start_price-self.stop_loss) / self.INSTRUMENTS[pair]['step'])* self.INSTRUMENTS[pair]['step_cost'])

        if self.QUANTITY >= MAX_LOTS:
            self.QUANTITY = MAX_LOTS

        create_order(pair, 'B', quantity)
        if self.QUANTITY % 2 == 0:
            self.order_quantity_1 = QUANTITY / 2
            self.order_quantity_2 = self.order_quantity_1
        else:
            self.order_quantity_1 = QUANTITY//2 + 1
            self.order_quantity_2 = QUANTITY - self.order_quantity_1



    async def execute_trading_strategy(self):
        while True: # -- Первый уровень
            action_price = float(get_price()[self.pair])

            if action_price >= (self.start_price - self.stop_loss) * 2 + self.start_price: # -- TakeProfit1
                create_order(self.pair, 'S', self.order_quantity_1)
                money = ((self.start_price - self.stop_loss) * 2 ) / self.INSTRUMENTS[pair]['step'] * self.INSTRUMENTS[pair]['step_cost']*self.order_quantity_1
                send_tg_message(f'[Level 1] Сработал TakeProfit +{money}')

                while True: # -- Второй уровень

                    action_price_2 = float(get_price()[self.pair])
                    if action_price_2 >= (self.start_price - self.stop_loss) * 2.5 + self.start_price: # -- TakeProfit2
                        create_order(self.pair, 'S', self.order_quantity_2)
                        money = ((self.start_price - self.stop_loss) * 2.5 ) / self.INSTRUMENTS[pair]['step'] * self.INSTRUMENTS[pair]['step_cost']*self.order_quantity_2
                        send_tg_message(f'[Level 2] Сработал TakeProfit +{money}')
                        return True

                    elif action_price_2 <= self.start_price:  # -- Stoploss2
                        create_order(self.pair, 'S', self.order_quantity_2)
                        if self.QUANTITY % 2 == 0:
                            send_tg_message(f'[Level 2] Сработал Stoploss 0')
                        else:
                            money = ((self.start_price - self.stop_loss) * 2 ) / self.INSTRUMENTS[pair]['step'] * self.INSTRUMENTS[pair]['step_cost']*self.order_quantity_1
                            send_tg_message(f'[Level 2] Сработал Stoploss +{money}')
                        return True
                    await asyncio.sleep(1)

            elif action_price <= self.stop_loss: # -- Stoploss1
                create_order(self.pair, 'S', self.QUANTITY)
                money = self.QUANTITY*(((self.start_price-self.stop_loss) / self.INSTRUMENTS[pair]['step'])* self.INSTRUMENTS[pair]['step_cost'])
                send_tg_message(f'[Level 1] Сработал Stoploss -{money}')
                return True

            await asyncio.sleep(1)


    def create_order(self, ticker, operation, quantity):
        with open('C:/QUIK_DATA/order.txt', 'w') as file:
            file.write(f'DEAL:{ticker}/{operation}/{quantity}')

    def monitoring_orders(self, ):
        with open('C:/QUIK_DATA/order_list.txt', 'r') as file:
            content = file.read()
            if content != '':
                return content
            else:
                return False