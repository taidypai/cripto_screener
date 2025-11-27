import asyncio
from finam_trade_api import Client, TokenManager

token = "eyJraWQiOiJkNjdlNTliMi1kODUyLTRjYzctYTFmNy04OWNlOTZkNWE3MGEiLCJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhcmVhIjoidHQiLCJwYXJlbnQiOiJiODlmOGQ2NC03ZTNlLTRmZjQtYjFlYy0xYzQ0NGE2MmVkZjgiLCJhcGlUb2tlblByb3BlcnRpZXMiOiJINHNJQUFBQUFBQUFfeldUUFhMYk1CQ0ZaWkdLTlVxM3BVdW44MHdLMlptSlU0SWdTTUVpU0JvQUpTb05HOWRKa1V0a0puVXVrQ2FWcjVJejVXRVhicjYzQUJZX3kzM2NfdnY1LXV2MWdkYmI0dVp2dVYzZnJ1NnVkNXNQdnZLMUJMcnlISnpQZXJ4N3R5dVZtd2RXci1la2xZcUI5ZVNhcEdZZVhWSnI1cGExTVpQb3hIbk9CdDQzREZHempsNnhSbDFsZFZtZms0NjIxMWx0MWk0cm56T0dsdk45bEhQOUpEb3JGMFNEeVNyejFlQkVfU1E2eWJxdW1xeFIxR2hSSi1zbWV0WkczanUzU3ZJT3h5WXIxenQzZFMtYTkzWDV2bTZRZWFkcTFsN0otM3FwZC03YlBNN3Y3aTk1X2lMalVjbjk0V0N5eW4zeEdGS0RscXJYbWdOZFdjNWNORHJDRV80eWNtQW1YM0hnWFBXVmczNzAzTTBsYUh1MzJSVkxrTXd3NW9Rd3Z1dzVpTjZFLTZ2Vm42djFiblh6dTl3V1ZDZ3pBOEVrUENkZ0NEc0F6d2xwQVItWHl1cjd0eGZhSlA2Z0FwODVBUW42WUFGbkVyQlRud3hkMTAtMnI5T3hacHFKdlVUWFRlTVc1X2RVTnJaWHRFdDBTejNGQzIyYUFXMm5vc0ZWNndhN1d1T3BPRFE0RXQyZ3dwb0ptSkRSNlF1UTd1clNzOUFEUUdPSHcyV2xjd3BQY2Y1RUJib0N1SVJnRTF3Q3FrTTdFamdLeFBhbFlnaUsyTGxNeDBRR1drVnNYS1psZGt4Y05oN0Rudm5BX0lSMFBJbDlUSVhYLURBLVZyVHhFXzQ4S29JYUFCTVNzQlJhbkFCOFJIZzRBQmFiUWtRaDRRekVHbFhIN2tSbFJFMElCeHdSTHpoaVVsZy1wOXBuYkNtVFcwZzhrd2F4WWFLdVJhY3lrblZJakVOaUc4eTF0U0t4RG9sQlNGeHh1M3J6eGUzN0w1XzNqNF8zX3VucGRQd1BQeE5QTVZvRUFBQSIsInNjb250ZXh0IjoiQ2hBSUJ4SU1kSEpoWkdWZllYQnBYM0oxQ2lnSUF4SWtZV0kxTlRFM01UY3RPR1kwWXkwMFpqSm1MVGxrTmpjdE5XSTNNbUkzT1RBNE5UVm1DZ1FJQlJJQUNna0lBQklGYUhSdGJEVUtLQWdDRWlRMU4yUXlObUppTUMxaU9ERTBMVEV4WmpBdFlqZ3pNaTFsT1RBMFl6SXdZakl4WVRnS0JRZ0lFZ0V6Q2dRSUNSSUFDZ2tJQ2hJRk1TNDJMalVLS0FnRUVpUmtOamRsTlRsaU1pMWtPRFV5TFRSall6Y3RZVEZtTnkwNE9XTmxPVFprTldFM01HRXlVQW9WVkZKQlJFVkJVRWxmUzFKQlZFOVRYMVJQUzBWT0VBRVlBU0FCS2dkRlJFOVlYMFJDT2dJSUEwb1RDZ01JaHdjU0JRaUhvWjRCR2dVSWg1YjRBVkNzQWxnQllBRm9BWElHVkhoQmRYUm8iLCJ6aXBwZWQiOnRydWUsImNyZWF0ZWQiOiIxNzY0MjY0ODc1IiwicmVuZXdFeHAiOiIxNzY0NDUwMDU5Iiwic2VzcyI6Ikg0c0lBQUFBQUFBQS8xTnFaT1JTTVUxTE1iSXdUVExRTlRPeE5OQTFNVEd5MExWSU1UTFh0VEJJVGpJek56Wk5ORGMyRU9LNk1PbkNoZ3RiTHV5NHNFZEs0TUxDQ3pzdU5sM1lDK1R0dXJEdndpWWwwYkxFbFB4aUF5TURNM016aC9UY3hNd2N2ZVQ4M0NRVlIxZEhNM01YUzFkZE0xZGpDMTBUSXlOalhRdExjemRkVjFOWEEzTkxRMU5uWXd2TEJNWmRqTHhjclBGK0FVSCtRaXorVHY0UkFDWkJJcnFXQUFBQSIsImlzcyI6InR4c2VydmVyIiwia2V5SWQiOiJkNjdlNTliMi1kODUyLTRjYzctYTFmNy04OWNlOTZkNWE3MGEiLCJ0eXBlIjoiQXBpVG9rZW4iLCJzZWNyZXRzIjoiSlRuZE9PanFBaEp1SDQ0TmVPOVRpUT09Iiwic2NvcGUiOiJHQUUiLCJ0c3RlcCI6ImZhbHNlIiwic3BpblJlcSI6ZmFsc2UsImV4cCI6MTc2NDQ0OTk5OSwic3BpbkV4cCI6IjE3NjQ0NTAwNTkiLCJqdGkiOiJhYjU1MTcxNy04ZjRjLTRmMmYtOWQ2Ny01YjcyYjc5MDg1NWYifQ.L8xWX8rP0B1ldEXKedPl0ITI0lePWNnmP8c3AA9Jh26d2BHiMbRDb8NSmApRPMgzKiK4lKLm2UjD0tr-I3Ku4A"
account_id = "1975473"


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

        balance_data = {
            'available': available_balance,
            'currency': 'RUB',
            'timestamp': str(datetime.now())
        }

        print(f"✓ Баланс Finam: {available_balance:.2f} RUB")
        return balance_data

    except Exception as e:
        print(f"❌ Ошибка получения баланса Finam: {e}")
        return None


async def update_balance_in_executive():
    """Обновление баланса в executive.txt"""
    balance_data = await get_finam_balance()

    if not balance_data:
        return False

    try:
        executive_file = "C:/QUIK_DATA/executive.txt"

        # Читаем существующий файл
        if os.path.exists(executive_file):
            with open(executive_file, 'r') as f:
                content = f.read()
        else:
            content = ""

        # Формируем секцию BALANCE
        balance_section = f"""
[BALANCE]
available: {balance_data['available']}
currency: {balance_data['currency']}
timestamp: {balance_data['timestamp']}
"""

        # Обновляем или добавляем секцию BALANCE
        if '[BALANCE]' in content:
            # Заменяем существующую секцию
            import re
            content = re.sub(r'\[BALANCE\].*?(?=\[|$)', balance_section, content, flags=re.DOTALL)
        else:
            # Добавляем новую секцию
            content += balance_section

        # Записываем обратно
        with open(executive_file, 'w') as f:
            f.write(content)

        print("✅ Баланс обновлен в executive.txt")
        return True

    except Exception as e:
        print(f"❌ Ошибка обновления баланса в файле: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(update_balance_in_executive())