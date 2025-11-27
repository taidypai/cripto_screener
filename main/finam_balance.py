import asyncio
from finam_trade_api import Client, TokenManager

token = "eyJraWQiOiIwMWYzZjZkNC1kYTA3LTQwNmItYWRkZC0xODZiZTI2M2IyYjMiLCJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhcmVhIjoidHQiLCJwYXJlbnQiOiJmYTI3ZDBmOS02YzlkLTQ2NjUtYjhiMS0zZWQ0ZGFjMzEwNzMiLCJhcGlUb2tlblByb3BlcnRpZXMiOiJINHNJQUFBQUFBQUFfeldUUFhMYk1CQ0ZaWkdLTlVxM3BVdW44MHdLT1pteFU0SWdTTUVpU0JvQUpTb05HOWRKa1pPa3lBWFNwRXVicS1RcTZmeXdpelRmV3dDTG4tVS1idl8tX3ZQOTN3T3R0OFhOcjNLN3ZsM2RYZTgyNzN6bGF3bDA1VGs0bl9WNDkyWlhLamNQckY3UFNTc1ZBLXZKTlVuTlBMcWsxc3d0YTJNbTBZbnpuQTI4YnhpaVpoMjlZbzI2eXVxeVBpY2RiYS16MnF4ZFZqNW5EQzNuLXlqbi1rbDBWaTZJQnBOVjVxdkJpZnBKZEpKMVhUVlpvNmpSb2s3V1RmU3NqYngzYnBYa0hZNU5WcTUzN3VwZU5PX3I4bjNkSVBOTzFheTlrdmYxVXVfY3QzbWMzOTFmOHZ4RnhxT1MtOFBCWkpYNzRqR2tCaTFWcnpVSHVyS2N1V2gwaENmOFplVEFUTDdpd0xucU13Zjk2TG1iUzlEMmJyTXJsaUNaWWN3SllYelpjeEM5Q2ZkWHE1OVg2OTNxNWtlNUxhaFFaZ2FDU1hoT3dCQjJBSjRUMGdJLUxwWFYxeTh2dEVuOFJnVS1jd0lTOU1FQ3ppUmdwejRadXE2ZmJGLW5ZODAwRTN1SnJwdkdMYzd2cVd4c3IyaVg2Slo2aWhmYU5BUGFUa1dEcTlZTmRyWEdVM0ZvY0NTNlFZVTFFekFobzlNWElOM1ZwV2VoQjRER0RvZkxTdWNVbnVMOGlRcDBCWEFKd1NhNEJGU0hkaVJ3RklqdFM4VVFGTEZ6bVk2SkRMU0syTGhNeS15WXVHdzhoajN6QV9NajB2RWs5akVWWHVQRC1GalJ4a180ODZnSWFnQk1TTUJTYUhFQzhCN2g0UUJZYkFvUmhZUXpFR3RVSGJzVGxSRTFJUnh3Ukx6Z2lFbGgtWnhxbjdHbFRHNGg4VXdheElhSnVoYWR5a2pXSVRFT2lXMHcxOWFLeERva0JpRnh4ZTNxdnk5dTMzNTYyRDgtM3Z1bnA5UHhGU08tUHd4YUJBQUEiLCJzY29udGV4dCI6IkNoQUlCeElNZEhKaFpHVmZZWEJwWDNKMUNpZ0lBeElrWldZMU9ETTVNRE10TmpBME1TMDBaVEkwTFdJNU1HRXRORGRrTm1WaE1HWXlNakl6Q2dRSUJSSUFDZ2tJQUJJRmFIUnRiRFVLS0FnQ0VpUTFOMlF5Tm1KaU1DMWlPREUwTFRFeFpqQXRZamd6TWkxbE9UQTBZekl3WWpJeFlUZ0tCUWdJRWdFekNnUUlDUklBQ2drSUNoSUZNUzQyTGpVS0tBZ0VFaVF3TVdZelpqWmtOQzFrWVRBM0xUUXdObUl0WVdSa1pDMHhPRFppWlRJMk0ySXlZak15VUFvVlZGSkJSRVZCVUVsZlMxSkJWRTlUWDFSUFMwVk9FQUVZQVNBQktnZEZSRTlZWDBSQ09nSUlBMG9UQ2dNSWh3Y1NCUWlIb1o0QkdnVUloNWJEQVZDc0FsZ0JZQUZvQVhJR1ZIaEJkWFJvIiwiemlwcGVkIjp0cnVlLCJjcmVhdGVkIjoiMTc2NDI4MDg2NCIsInJlbmV3RXhwIjoiMTkyMjMwMjg1OSIsInNlc3MiOiJINHNJQUFBQUFBQUEvMU5xWk9SU01VMUxNYkl3VFRMUU5UT3hOTkExTVRHeTBMVklNVExYdFRCSVRqSXpOelpOTkRjMkVPSzZNT25DaGd0Ykx1eTRzRWRLNE1MQ0N6c3VObDNZQytUdHVyRHZ3aVlsMGJMRWxQeGlBeU1ETTNNemgvVGN4TXdjdmVUODNDUVZSMWRITTNNWFMxZGRNMWRqQzEwVEl5TmpYUXRMY3pkZFYxTlhBM05MUTFObll3dkxYWXk4WEt6eGZnRkIva0lzL2s3K0VRRGs0WnNtbEFBQUFBIiwiaXNzIjoidHhzZXJ2ZXIiLCJrZXlJZCI6IjAxZjNmNmQ0LWRhMDctNDA2Yi1hZGRkLTE4NmJlMjYzYjJiMyIsInR5cGUiOiJBcGlUb2tlbiIsInNlY3JldHMiOiJ1T3QzRTZGMUZEdXJzUWdwT3pkM2RnPT0iLCJzY29wZSI6IiIsInRzdGVwIjoiZmFsc2UiLCJzcGluUmVxIjpmYWxzZSwiZXhwIjoxOTIyMzAyNzk5LCJzcGluRXhwIjoiMTkyMjMwMjg1OSIsImp0aSI6ImVmNTgzOTAzLTYwNDEtNGUyNC1iOTBhLTQ3ZDZlYTBmMjIyMyJ9.LsqI66j3sZ3T3qVNA_LrpaeCtJ8VyihdEt1TQsGuXzgFgPhUyIYTSrvYlhgVucj_1dw8lQPRf4wNxLUr7MPhQw"
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
