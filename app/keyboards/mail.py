from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def mail_go_kb():
    kb = [
        [KeyboardButton(text="/go")],
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, input_field_placeholder="Начнем?")
    return keyboard
