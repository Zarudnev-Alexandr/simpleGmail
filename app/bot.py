import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from app.db.database import init_models
from app.db.utils import get_my_connected_mail, change_is_launched, get_is_launched_status, get_all_connected_mails
from config_reader import config
from app.handlers import mail, start
from aiogram.fsm.storage.memory import MemoryStorage
from app.utils.mail import distribution_mail

username1 = "alexandrzarudnev57@gmail.com"
app_password1 = "ksqk uuwe tpuf lljx"

username2 = "sashazarudnev107@gmail.com"
app_password2 = "xltk ibjq bnif yrdd"

# MAX_MESSAGE_LENGTH = 3500

gmail_host = "imap.gmail.com"

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

bot = Bot(token=config.bot_token.get_secret_value(), parse_mode="HTML")

dp = Dispatcher(storage=MemoryStorage())

dp.include_routers(mail.router)
dp.include_routers(start.router)

active_tasks = {}


@dp.message(F.text.lower() == "🚀запустить")
async def go(message1: Message):
    user_id = message1.from_user.id
    my_mail_result = await get_my_connected_mail(user_id=user_id)
    current_status = await get_is_launched_status(user_id)
    if not my_mail_result:
        await message1.answer(text="Почта не подключена❌\nПерейдите в меню снизу и выберите <i>Подключить почту</i>↘")
        return
    if current_status:
        await message1.answer(text="Рассылка уже запущена, вы получаете все текущие письма, отправленные вам на почту")
    else:
        await change_is_launched(user_id)
        await message1.answer(text="Рассылка запущена")
        # Отменяем активную задачу перед запуском новой задачи
        active_task = active_tasks.get(user_id)
        if active_task:
            active_task.cancel()
            del active_tasks[user_id]
        new_task = asyncio.create_task(distribution_mail(user_id, bot, {'mail': my_mail_result[0].mail, 'hashed_password':
            my_mail_result[0].hashed_password}, ))
        # Сохраняем новую задачу в словаре
        active_tasks[user_id] = new_task


@dp.message(F.text.lower() == "❌отменить рассылку")
async def cancel_distribution(message: Message):
    user_id = message.from_user.id
    current_status = await get_is_launched_status(user_id)
    if current_status:
        try:
            # Отменяем активную задачу перед отменой рассылки
            active_task = active_tasks.get(user_id)
            if active_task:
                await asyncio.shield(active_task.cancel())  # Изолируем задачу от отмены
                del active_tasks[user_id]
        except asyncio.CancelledError:
            pass  # Обработка отмены задачи, чтобы не влиять на остальной код
        finally:
            await change_is_launched(user_id)
            await message.answer(text="Рассылка отменена, чтобы снова получать письма, нажмите на <i>🚀Запустить</i> на "
                                      "клавиатуре снизу ↘")
    else:
        await message.answer(text="Рассылка уже отменена. Чтобы снова получать письма, нажмите на <i>🚀Запустить</i> на "
                                  "клавиатуре снизу ↘")


async def main():
    try:
        await init_models()
        users = await get_all_connected_mails()

        tasks = []

        for item in users:
            if item.is_launched:
                task = asyncio.create_task(
                    distribution_mail(item.user_id, bot, {'mail': item.mail, 'hashed_password': item.hashed_password}))
                tasks.append(task)
                # Сохраняем задачу в словаре
                active_tasks[item.user_id] = task

        polling_task = dp.start_polling(bot)
        tasks.append(polling_task)

        await asyncio.gather(*tasks, return_exceptions=True)  # Используем return_exceptions=True

    except asyncio.CancelledError:
        print("Some tasks were cancelled, but the bot continues running.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
