from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Trade & Brain", url="t.me/trade_and_brain"),
    )
    builder.row(
        InlineKeyboardButton(text="Позиция", callback_data="lot"),
        InlineKeyboardButton(text="levels", callback_data="add_levels")
    )
    return builder.as_markup()

def add_level_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="IMOEX", callback_data="pair_imoex"),
    )
    builder.row(
        InlineKeyboardButton(text="GLDRUBF", callback_data="pair_gldrubf"),
        InlineKeyboardButton(text="NASD", callback_data="pair_nasd")
    )
    builder.row(
        InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_main")
    )
    return builder.as_markup()