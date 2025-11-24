import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from services.level_service import level_service
import keyboards
from handlers.callback_routers import LevelStates

logger = logging.getLogger(__name__)
message_router = Router()

@message_router.message(LevelStates.waiting_for_price)
async def handle_price_input(message: Message, state: FSMContext):
    """Обработка ввода цены уровня"""
    try:
        user_id = message.from_user.id
        price_text = message.text.strip()

        # Проверяем, что введено число
        try:
            price = float(price_text.replace(',', '.'))
        except ValueError:
            await message.answer(
                "❌ Неверный формат цены! Введите число (например: 123.45):"
            )
            return

        # Получаем выбранную пару из состояния
        state_data = await state.get_data()
        selected_pair = state_data.get('selected_pair')

        if not selected_pair:
            await message.answer("❌ Ошибка: не выбрана пара. Начните заново.")
            await state.clear()
            return

        # Добавляем уровень
        level_service.add_level(user_id, selected_pair, price)

        # Получаем обновленный список уровней пользователя
        user_levels = level_service.get_user_levels(user_id)

        # Формируем сообщение с уровнями
        levels_text = "📈 Ваши текущие уровни:\n\n"
        if user_levels:
            for pair, levels in user_levels.items():
                levels_text += f"*{pair}*:\n"
                for level in levels:
                    levels_text += f"  • {level['price']}\n"
                levels_text += "\n"
        else:
            levels_text += "Уровней пока нет\n"

        levels_text += f"\n✅ Уровень *{price}* для пары *{selected_pair}* добавлен!"

        # Возвращаем в главное меню
        await message.answer(
            levels_text,
            reply_markup=keyboards.main_keyboard(),
            parse_mode='Markdown'
        )

        # Очищаем состояние
        await state.clear()

    except Exception as e:
        logger.error(f"Error handling price input: {e}")
        await message.answer(
            "❌ Произошла ошибка при добавлении уровня.",
            reply_markup=keyboards.main_keyboard()
        )
        await state.clear()