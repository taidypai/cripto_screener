import asyncio
from finam_trade_api import Client, TokenManager
import os
import sys
from datetime import datetime

sys.path.append(r"C:\Users\Вадим\Documents\python\trade-brain-main")
import config

token = config.finam_api_token
account_id = config.finam_api_account_id

async def get_finam_balance():
    """Получение баланса с Finam"""
    client = Client(TokenManager(token))
    await client.access_tokens.set_jwt_token()

    try:
        # Получение информации об аккаунте
        account_info = await client.account.get_account_info(account_id)

        # Ищем денежные средства в рублях
        available_balance = 0.0
        for cash in account_info.cash:
            if cash.currency_code == 'RUB':
                # Конвертируем FinamMoney в обычное число
                amount = float(cash.units) + (float(cash.nanos) / 1_000_000_000)
                available_balance = amount
                break
        return available_balance
    except Exception as e:
        print(f"Ошибка получения баланса Finam: {e}")
        return None


def balance_main():
    balance = asyncio.run(get_finam_balance())
    return balance

if __name__ == "__main__":
    print(balance_main())


