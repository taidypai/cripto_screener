import logging
from aiogram.filters import Command, CommandStart
from aiogram import types, Router
import asyncio

import keyboards

logger = logging.getLogger(__name__)
start_router = Router()

@start_router.message(CommandStart())
async def handle_start(message: types.Message):
    """Обработка команды /start"""
    try:
        user_id = message.from_user.id

        welcome_text = "Добро пожаловать в экосистему *Trade & Brain*!"
        await message.answer(welcome_text, reply_markup=keyboards.main_keyboard(), parse_mode='Markdown')
        await asyncio.sleep(2)

    except Exception as e:
        logger.error(f"Error in start handler: {e}")
        await message.answer("Произошла ошибка при запуске бота")