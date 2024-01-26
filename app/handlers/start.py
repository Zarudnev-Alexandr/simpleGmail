from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.utils import add_user
from app.keyboards.start import start_kb, start_instruction_kb, start_reply_keyboard_markup

router = Router()


def get_start_text() -> str:
    return ("🔥<b>Добро пожаловать в simpleGmail бота</b>🔥\n\n Что я умею?\n\n"
            "✉В реальном времени отправлять сообщения, приходящие вам на google почту\n\n"
            "⚙Настраивать белый список, чтобы смотреть сообщения только от нужных людей\n\n"
            "🤡Веселить вас ломаной HTMl разметкой, ведь телеграм - он такой\n\n"
            "<b>Что ж, давайте начнем! Все пункты меню снизу в клавиатуре↘</b>")


@router.message(Command('start'))
async def start(message: Message):
    user_id = message.from_user.id
    welcome_message = await add_user(user_id=user_id)

    await message.answer(welcome_message)
    await message.answer(get_start_text(), reply_markup=start_reply_keyboard_markup())


# @router.callback_query(F.data.startswith("start_back_to_main"))
# async def callbacks_start_main(callback: CallbackQuery):
#     await callback.message.edit_text(get_start_text(), reply_markup=start_kb())


@router.message(F.text.lower() == "📃инструкция")
async def get_instruction(message: Message):
    await message.delete()
    await message.answer(text="📃<b>Инструкция</b>📃\n\n"
                                           "Для того чтобы просматривать сообщения, отправленные на почту, "
                                              "в телеграме, "
                                              "нужно провести небольшую "
                                           "настройку, а именно, узнать пароль приложения от своей google почты.\n\n"
                                           "1) Заходим на сайт https://myaccount.google.com\n"
                                           "2) Переходим на вкладку '<i>Безопасность</i>' (она слева, рядом с другими "
                                           "вкладками)\n"
                                           "3) Листаем до блока 'Вход в Google' и нажимаем на '<i>Двухэтапная "
                                           "аутентификация</i>'\n"
                                           "3.1) Если Двухэтапная аутентификация не подключена - подключаем\n"
                                           "4) Листаем на открывшейся странице в самый низ, пока не найдем 'Пароли "
                                           "приложений'\n"
                                           "5) Нажимаем на стрелочку '<b>></b>' и генерируем пароль приложения ("
                                           "название "
                                           "можете указать любое, например, 'Telegram')\n"
                                           "6) После нажатия на кнопку 'Создать', появится окно с вашим паролем. "
                                           "Копируем его "
                                           "куда-нибудь, так как после закрытия окна, мы его никогда не увидим!\n\n"
                                           "<b>Отлично! Пароль мы получили, осталось совсем немного</b>\n\n"
                                           "7) Заходим в нашу почту https://mail.google.com/mail и справа сверху "
                                           "видим шестеренку. Нажимаем на нее и открываем '<i>Все настройки</i>'\n"
                                           "8) В открывшейся окне выбираем вкладку '<i>Пересылка и POP/IMAP</i>' (она "
                                           "находится сверху)\n"
                                           "9) Нажимаем на '<i>Включить IMAP</i>'. Сохраняем изменения\n"
                                           "10) Вот и все! Удачного использования бота.",)



