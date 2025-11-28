import sys
sys.path.append(r"C:\Users\Вадим\Documents\python\trade-brain-main")
from components.send_telegram_message import send_tg_message
from trading_engine.louncher import Louncher_trade_engine

async def trade_main():
    """Асинхронная главная функция"""
    while True:
        line = Louncher_trade_engine.monitoring_orders()
        if line:
            try:
                parts = line.split(':')
                pair = parts[0]      # 'GLDRUBF'
                stop_loss = parts[1]       # '1045.4'

                # Создаем экземпляр и запускаем стратегию
                trade_engine = Louncher_trade_engine(pair, stop_loss)

                # Запускаем асинхронную стратегию с await
                success = await trade_engine.execute_trading_strategy()

                if success:
                    send_tg_message('Сделка успешно завершена')

            except Exception as e:
                print(f"Ошибка при обработке ордера: {e}")
                send_tg_message(f'Ошибка в торговом движке: {e}')

        await asyncio.sleep(1)


if __name__ == "__main__":
    # Запускаем асинхронную main функцию
    asyncio.run(main())