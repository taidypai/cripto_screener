import asyncio
import logging
from aiogram import Dispatcher

from config import bot
from handlers.start_router import start_router
from handlers.callback_routers import callback_router
from handlers.message_router import message_router  # Добавьте этот импорт

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def on_startup():
    """Действия при запуске бота"""
    logger.info("Бот запущен...")
    # Убрал синхронизацию времени Binance, так как она не используется
    logger.info("Level service initialized")

async def on_shutdown():
    """Действия при остановке бота"""
    logger.info("Бот остановлен...")
    await bot.session.close()

async def main():
    """Основная функция запуска бота"""
    dp = Dispatcher()

    # Регистрируем роутеры
    dp.include_router(start_router)
    dp.include_router(message_router)  # Добавьте эту строку
    dp.include_router(callback_router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    cleanup_task_instance = asyncio.create_task(cleanup_task())

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка в боте: {e}")
    finally:
        cleanup_task_instance.cancel()
        await on_shutdown()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")