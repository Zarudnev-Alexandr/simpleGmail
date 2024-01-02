from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def mail_go_kb():
    kb = [
        [KeyboardButton(text="/go")],
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, input_field_placeholder="Начнем?")
    return keyboard


def mail_white_list():
    buttons = [
        [
            InlineKeyboardButton(text="💌Добавить почту", callback_data="whiteList_addWhiteList"),
            InlineKeyboardButton(text="👀Показать белый список", callback_data="whiteList_shwoWhiteList")
        ],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def mail_white_list_after_enter_kb():
    buttons = [
        [
            InlineKeyboardButton(text="➕Добавить еще", callback_data="whiteListAfterEnter_add"),
            InlineKeyboardButton(text="🚪Выйти", callback_data="whiteListAfterEnter_leave")
        ],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard
