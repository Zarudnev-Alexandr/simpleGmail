import imaplib
import email
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from bs4 import BeautifulSoup

from app.db.database import init_models
from app.db.utils import get_my_connected_mail
from config_reader import config
from app.handlers import mail, start
from aiogram.fsm.storage.memory import MemoryStorage
from app.handlers.mail import users_data
import html2text
from app.utils.mail import convert_date, decode_email_header, decode_email_subject, connect_to_mail_class
import re

username1 = "alexandrzarudnev57@gmail.com"
app_password1 = "ksqk uuwe tpuf lljx"

username2 = "sashazarudnev107@gmail.com"
app_password2 = "xltk ibjq bnif yrdd"

MAX_MESSAGE_LENGTH = 3500

gmail_host = "imap.gmail.com"

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

bot = Bot(token=config.bot_token.get_secret_value(), parse_mode="HTML")

dp = Dispatcher(storage=MemoryStorage())

dp.include_routers(mail.router)
dp.include_routers(start.router)


@dp.message(F.text.lower() == "🚀запустить")
async def go(message1: Message):
    user_id = message1.from_user.id
    h = html2text.HTML2Text()
    last_processed_uid = None
    my_mail_result = await get_my_connected_mail(user_id=user_id)
    if not my_mail_result:
        await message1.answer(text="Почта не подключена❌\nПерейдите в меню снизу и выберите <i>Подключить почту</i>↘")
        return

    while True:
        mail = connect_to_mail_class(my_mail_result[0])
        mail.select("INBOX")
        _, message_numbers = mail.search(None, 'ALL')
        uids = message_numbers[0].split()
        if uids:
            latest_uid = uids[-1]

            # Если это первый запуск или есть новые сообщения
            if last_processed_uid is None or latest_uid != last_processed_uid:
                _, data = mail.fetch(latest_uid, '(RFC822)')
                _, bytes_data = data[0]

                email_message = email.message_from_bytes(bytes_data)

                for part in email_message.walk():
                    if part.get_content_type() == "text/plain" or part.get_content_type() == "text/html":
                        message = part.get_payload(decode=True)
                        html_content = message.decode()

                        soup = BeautifulSoup(html_content, 'html.parser')
                        clean_text = soup.get_text(separator='\n', strip=True)
                        clean_text = clean_text.replace('<', '&lt;').replace('>', '&gt;')

                # Move these lines outside the loop
                text_parts = [clean_text[i:i + MAX_MESSAGE_LENGTH] for i in
                              range(0, len(clean_text), MAX_MESSAGE_LENGTH)]

                # Отправляем каждую часть текста поочередно
                for part in text_parts:
                    send_data = f"<b>📬{h.handle(decode_email_subject(email_message['subject']))}<i>📅{h.handle(convert_date(email_message['date']))}</i>✍{h.handle(decode_email_header(email_message['from']))}</b>{part}"
                    await message1.answer(send_data, parse_mode=ParseMode.HTML)

                # Обновление переменной last_processed_uid
                last_processed_uid = latest_uid

        # close the connection
        mail.close()
        mail.logout()
        await asyncio.sleep(5)


async def main():
    await init_models()
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

