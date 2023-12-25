from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from email_validator import validate_email, EmailNotValidError

from app.db.utils import add_connected_email, get_my_connected_mail
from app.keyboards.mail import mail_go_kb
from app.utils.mail import check_format_password, connect_to_mail_dict

router = Router()
users_data = {}


class RegistrationStates(StatesGroup):
    waiting_for_email = State()
    waiting_for_password = State()


@router.message(F.text.lower() == "📬моя почта")
async def mail_my_mail(message: Message):
    user_id = message.from_user.id
    my_mail_result = await get_my_connected_mail(user_id=user_id)

    if not my_mail_result:
        await message.answer(text="Почта не подключена❌\nПерейдите в меню снизу и выберите <i>Подключить почту</i>↘")
        await message.delete()
    else:
        my_mail = my_mail_result[0]  # Extract the ConnectedMail object from the tuple
        email_address = my_mail.mail
        await message.answer(text=f"Ваша почта подключена✅\nEmail: {email_address}")
        await message.delete()


@router.message(StateFilter(None), F.text.lower() == "💌подключить почту")
async def mail_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    connected_mail = await get_my_connected_mail(user_id=user_id)
    print(connected_mail)
    if not connected_mail:
        await message.answer("Вы собираетесь подключить почту. Если поймете, что ввели что-то неправильно, "
                             "просто напишите <i>отмена</i> или <i>/cancel</i>")
        await message.answer("Укажите почту в формате <b>your_gmail</b>@gmail.com:")
        await message.delete()
        await state.set_state(RegistrationStates.waiting_for_email)
    else:
        await message.answer("Почта уже подключена😎")
        await message.delete()
        await state.clear()
        return


@router.message(Command(commands=["cancel"]))
@router.message(F.text.lower() == "отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.delete()
    await message.answer(
        text="Ввод отменен",
    )


@router.message(RegistrationStates.waiting_for_email, F.text)
async def mail_typing(message: Message, state: FSMContext):
    email = message.text

    # Валидация почты
    try:
        v = validate_email(email)
        email = v.normalized
    except EmailNotValidError:
        await message.answer("Неправильный формат почты, введите заново: ")
        return

    await state.update_data(email=email)
    await message.answer(text="Введите пароль в формате <b>xxxx xxxx xxxx xxxx</b>:")
    await state.set_state(RegistrationStates.waiting_for_password)


@router.message(RegistrationStates.waiting_for_password, F.text)
async def password_typing(message: Message, state: FSMContext):
    password = message.text
    if check_format_password(password):
        await state.update_data(password=message.text)
        user_data = await state.get_data()

        # Создаем клавиатуру с кнопками
        buttons = [
            [
                InlineKeyboardButton(text="Все верно", callback_data="mail_confirm"),
                InlineKeyboardButton(text="Перепишем", callback_data="mail_rewrite")
            ],
        ]
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        await message.answer(
            text=f"Ваш email: {user_data['email']}\nВаш пароль: {user_data['password']}",
            reply_markup=keyboard
        )
    else:
        # Сообщение об ошибке
        await message.answer("Неправильный формат пароля, введите заново:")


@router.callback_query(F.data.startswith("mail_"))
async def callbacks_mail(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    user_id = callback.from_user.id
    user_data = await state.get_data()

    if action == "confirm":
        mail_connection = connect_to_mail_dict({'mail': user_data['email'], 'hashed_password': user_data['password']})
        if mail_connection == "LoginFatal":
            await callback.message.answer('❌Неверная почта или пароль приложения. Проверьте все еще раз и снова '
                                          'нажмите на '
                                          '"<i>Подключить почту</i>" в клавиатуре снизу↘')
            await state.clear()
            return

        answer_message = await add_connected_email(mail=user_data['email'], password=user_data['password'],
                                                   user_id=user_id)
        await callback.message.answer(answer_message)

        await callback.message.edit_text("Ваши данные сохранены!")
        await state.clear()
    elif action == "rewrite":
        await callback.message.edit_text("Давайте начнем заново.")
        await state.set_state(RegistrationStates.waiting_for_email)
        await mail_start(callback.message, state)



