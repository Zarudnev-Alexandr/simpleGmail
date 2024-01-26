from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from email_validator import validate_email, EmailNotValidError

from app.db.utils import add_connected_email, get_my_connected_mail, get_user_by_id, add_mail_to_white_list, \
    get_white_list, change_is_launched, get_is_launched_status, delete_connected_email, remove_mail_from_white_list, \
    get_is_whitelist_active_status, change_is_whitelist_active
from app.keyboards.mail import mail_go_kb, mail_white_list, mail_white_list_after_enter_kb, my_mail_kb, \
    mail_white_list_after_remove_kb
from app.utils.mail import check_format_password, connect_to_mail_dict, validate_and_normalize_email, format_email_list, \
    send_whitelist_page

router = Router()


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
        await message.answer(text=f"Ваша почта подключена✅\nEmail: {email_address}", reply_markup=my_mail_kb())
        await message.delete()


@router.callback_query(F.data.startswith("mymail_remove"))
async def callback_my_mail(callback: CallbackQuery):
    user_id = callback.from_user.id
    my_mail_result = await get_my_connected_mail(user_id=user_id)
    if not my_mail_result:
        await callback.message.answer(text="Почта не подключена, отвязывать нечего❌")
        await callback.message.delete()
        return
    if my_mail_result[0].is_launched:
        await callback.message.answer(text="У вас включена рассылка, в начале отключите ее, выбрав '<i>❌Отменить "
                                           "рассылку</i>' в клавиатуре снизу ↘")
        await callback.message.delete()
        return
    else:
        await delete_connected_email(user_id)
        await callback.message.answer(text="Почта успешно отвязана✅")
        await callback.message.delete()
        return


@router.message(Command(commands=["cancel"]))
@router.message(F.text.lower() == "отмена")
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.delete()
    await message.answer(
        text="Ввод отменен",
    )


class WhitelistState(StatesGroup):
    waiting_for_email = State()
    waiting_for_remove_email = State()


@router.message(F.text.lower() == "✅белый список")
async def white_list(message: Message):
    user_id = message.from_user.id
    current_user = await get_user_by_id(user_id)
    is_whitelist_active = 'включено' if await get_is_whitelist_active_status(user_id) else 'отключено'
    if current_user:
        await message.answer(text="✅Белый список✅\n\n"
                                  f"Статус: {is_whitelist_active}\n"
                                  "Здесь можно увидеть добавленные вами почты. Если список пуст, то вам будут "
                                  "приходить все сообщения.", reply_markup=mail_white_list())
        await message.delete()


@router.callback_query(StateFilter(None), F.data.startswith("whiteList_"))
async def callbacks_whiteList(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    user_id = callback.from_user.id
    user = await get_user_by_id(user_id)
    if action == "addWhiteList":
        await callback.message.answer(text="Укажите почту (формат: xxx@xxx.xxx): ")
        await callback.message.delete()
        await state.set_state(WhitelistState.waiting_for_email)

    elif action == "shwoWhiteList":
        whitelist = await get_white_list(user_id)

        current_page = 1
        await send_whitelist_page(current_page, callback.message, whitelist)

    elif action == "removeMail":
        await callback.message.answer(text="Укажите почту (формат: xxx@xxx.xxx): ")
        await state.set_state(WhitelistState.waiting_for_remove_email)

    elif action == "changeStatus":
        change_is_whitelist_active_state = await change_is_whitelist_active(user_id)
        await callback.message.answer(change_is_whitelist_active_state)
        await callback.message.delete()


@router.callback_query(lambda c: c.data.startswith('whitelist_prev_page_') or c.data.startswith('whitelist_next_page_'))
async def process_pagination_callback(callback: CallbackQuery):
    page = int(callback.data.split('_')[-1])
    user_id = callback.from_user.id
    whitelist = await get_white_list(user_id)

    if callback.data.startswith('whitelist_prev_page_'):
        page -= 1
    elif callback.data.startswith('whitelist_next_page_'):
        page += 1

    await send_whitelist_page(page, callback.message, whitelist)
    await callback.answer()


@router.message(WhitelistState.waiting_for_email, F.text)
async def whitelist_mail_typing(message: Message, state: FSMContext):
    email = message.text
    user_id = message.from_user.id

    if validate_and_normalize_email(email) is not None:
        email_add = await add_mail_to_white_list(email, user_id)
        if email_add == 404:
            await message.answer(text="Не удалось добавить почту😢")
            await state.clear()
            return
        elif email_add == 201:
            await message.answer(text=f"Почта {email} успешно добавлена в белый список✅",
                                 reply_markup=mail_white_list_after_enter_kb())
        elif email_add == 409:
            await message.answer(text="Вы уже добавляли эту почту, давайте что-нибудь новенькое😕\nВведите почту "
                                      "заново: ")
    else:
        await message.answer("Неправильный формат почты, введите заново: ")


@router.message(WhitelistState.waiting_for_remove_email, F.text)
async def whitelist_mail_remove_typing(message: Message, state: FSMContext):
    email = message.text
    user_id = message.from_user.id

    if validate_and_normalize_email(email) is not None:
        email_remove = await remove_mail_from_white_list(email, user_id)
        print(email_remove)
        if email_remove == 404:
            await message.answer(text="Не удалось удалить почту😢")
            await state.clear()
            return
        elif email_remove == 200:
            await message.answer(text=f"Почта {email} успешно удалена из белого списка✅",
                                 reply_markup=mail_white_list_after_remove_kb())
    else:
        await message.answer("Неправильный формат почты, введите заново: ")


@router.callback_query(F.data.startswith("whiteListAfterEnter_"))
async def callbacks_whiteList(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    if action == "add":
        await callback.message.answer("Давайте еще пополним белый список.\nУкажите почту (формат: xxx@xxx.xxx): ")
        await callback.message.delete()
        await state.set_state(WhitelistState.waiting_for_email)
    elif action == "leave":
        await callback.message.answer("‍🔧Белый список успешно пополнен")
        await callback.message.delete()
        await state.clear()


@router.callback_query(F.data.startswith("whiteListAfterRemove_"))
async def callbacks_whiteList_remove(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    if action == "remove":
        await callback.message.answer("Давайте еще очистим белый список.\nУкажите почту (формат: xxx@xxx.xxx): ")
        await callback.message.delete()
        await state.set_state(WhitelistState.waiting_for_remove_email)
    elif action == "leave":
        await callback.message.answer("‍🔧Белый список успешно отредактирован")
        await callback.message.delete()
        await state.clear()


class RegistrationStates(StatesGroup):
    waiting_for_email = State()
    waiting_for_password = State()


@router.message(StateFilter(None), F.text.lower() == "💌подключить почту")
async def mail_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    connected_mail = await get_my_connected_mail(user_id=user_id)
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
