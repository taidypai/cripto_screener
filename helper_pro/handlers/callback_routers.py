import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import keyboards
from services.level_service import level_service

logger = logging.getLogger(__name__)
callback_router = Router()

# Состояния для FSM
class LevelStates(StatesGroup):
    waiting_for_price = State()

@callback_router.callback_query(F.data == "add_levels")
async def handle_add_levels_callback(callback: CallbackQuery):
    """Обработка нажатия на кнопку levels"""
    try:
        user_id = callback.from_user.id

        # Меняем сообщение на клавиатуру с парами
        await callback.message.edit_text(
            "📊 Выберите торговую пару для добавления уровня:",
            reply_markup=keyboards.add_level_keyboard()
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error in add_levels callback: {e}")
        await callback.answer("Произошла ошибка")

@callback_router.callback_query(F.data.startswith("pair_"))
async def handle_pair_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора торговой пары"""
    try:
        user_id = callback.from_user.id
        pair = callback.data.replace("pair_", "").upper()

        # Сохраняем выбранную пару в состоянии
        await state.update_data(selected_pair=pair)
        await state.set_state(LevelStates.waiting_for_price)

        # Просим ввести цену
        await callback.message.edit_text(
            f"💵 Вы выбрали пару: *{pair}*\n\n"
            f"Введите цену уровня (например: 123.45):",
            parse_mode='Markdown'
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error in pair selection: {e}")
        await callback.answer("Произошла ошибка")

@callback_router.callback_query(F.data == "back_to_main")
async def handle_back_to_main(callback: CallbackQuery, state: FSMContext):
    """Возврат к главному меню"""
    try:
        # Очищаем состояние
        await state.clear()

        # Возвращаем главное меню
        await callback.message.edit_text(
            "Добро пожаловать в экосистему *Trade & Brain*!",
            reply_markup=keyboards.main_keyboard(),
            parse_mode='Markdown'
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error in back to main: {e}")
        await callback.answer("Произошла ошибка")