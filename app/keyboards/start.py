from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup


def start_kb() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="📃Инструкция", callback_data="start_instruction"),
            # InlineKeyboardButton(text="💌Подключить почту", callback_data="connect_mail_command"),
        ],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def start_instruction_kb() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="👈Назад на Главную", callback_data="start_back_to_main")
        ],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def start_reply_keyboard_markup():
    kb = [
        [
            KeyboardButton(text="💌Подключить почту"),
            KeyboardButton(text="📬Моя почта"),
        ],
        [
            KeyboardButton(text="✅Белый список"),
            KeyboardButton(text="📃Инструкция"),
        ],
        [
            KeyboardButton(text="🚀Запустить"),
            KeyboardButton(text="❌Отменить рассылку")
        ],
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Что хотите сделать?",
    )
    return keyboard
