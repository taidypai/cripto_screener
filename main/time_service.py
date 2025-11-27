# time_service.py
import asyncio
from datetime import datetime, timedelta
import aiohttp
import pytz

class TimeService:
    def __init__(self):
        self.timeframe_minutes = {
            '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '4h': 240, '1d': 1440
        }
        self.use_binance_time = False
        self.last_sync_time = 0
        self.binance_server_time_diff = 0

    async def get_time_to_candle_close(self, timeframe):
        """Время до закрытия свечи для таймфрейма"""
        now = datetime.now()
        tf_minutes = {'5m': 5, '15m': 15, '1h': 60, '4h': 240, '1d': 1440}

        minutes = tf_minutes.get(timeframe, 60)
        total_minutes = now.hour * 60 + now.minute
        next_candle = ((total_minutes // minutes) + 1) * minutes

        # Обрабатываем случай, когда next_candle >= 1440 (24 часа)
        if next_candle >= 1440:
            # Переход на следующий день
            next_run = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            next_run += timedelta(minutes=next_candle - 1440)
        else:
            # Остаемся в текущих сутках
            next_hour = next_candle // 60
            next_minute = next_candle % 60
            next_run = now.replace(hour=next_hour, minute=next_minute, second=0, microsecond=0)

            # Если время уже прошло, добавляем день
            if next_run < now:
                next_run += timedelta(days=1)
        return (next_run - now).total_seconds()

    async def format_time_remaining(self, seconds):
        seconds = int(seconds)
        if seconds >= 3600:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        elif seconds >= 60:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes:02d}:{secs:02d}"
        else:
            return f"{seconds:02d}с"

async def main(time_frame):
    time_service = TimeService()
    my_time = await time_service.get_time_to_candle_close(time_frame)
    formatted_time = await time_service.format_time_remaining(my_time)
    print(f"Время до следующей свечи: {formatted_time}")

if __name__ == "__main__":
    time_frame = str(input('Введите TimeFrame: '))
    asyncio.run(main(time_frame))