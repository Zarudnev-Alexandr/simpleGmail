import imaplib
import email
import time
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from config_reader import config
from handlers import mail
from aiogram.fsm.storage.memory import MemoryStorage
from handlers.mail import users_data
import html2text
from utils.mail import convert_date, decode_email_header, decode_email_subject
import re

username1 = "alexandrzarudnev57@gmail.com"

app_password1 = "ksqk uuwe tpuf lljx"

MAX_MESSAGE_LENGTH = 3500

gmail_host = "imap.gmail.com"

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

bot = Bot(token=config.bot_token.get_secret_value(), parse_mode="HTML")

dp = Dispatcher(storage=MemoryStorage())

dp.include_routers(mail.router)


@dp.message(Command('get'))
async def get_me(message: Message):
    await message.answer(text=f"чек консоль")
    print("users_data = ", users_data)


@dp.message(Command('go'))
async def go(message1: Message):
    user_id = message1.from_user.id
    h = html2text.HTML2Text()
    last_processed_uid = None

    if user_id not in users_data:
        while True:
            try:
                mail = imaplib.IMAP4_SSL(gmail_host)
                mail.login(username1, app_password1)
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

                                no_template_text = re.sub(r"<template[\s\S]*?</template>|#shadow-root", "",
                                                          html_content, flags=re.IGNORECASE)
                                no_styles_text = re.sub(r"<style[\s\S]*?</style>", "", no_template_text,
                                                        flags=re.IGNORECASE)
                                plain_text = re.sub(r"<[^>]+>", "", no_styles_text, flags=re.S)
                                clean_text = re.sub(r'\n\s*\n', '\n', plain_text)

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

            except Exception as e:
                print(f"An error occurred: {e}")

            # Пауза между проверками (например, каждые 60 секунд)
            time.sleep(5)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())