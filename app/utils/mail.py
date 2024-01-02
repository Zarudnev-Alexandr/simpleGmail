import base64
import email
import imaplib
from datetime import datetime
import re
from email.header import decode_header
import html2text
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bs4 import BeautifulSoup
from email_validator import validate_email, EmailNotValidError

days_of_week = {
    "Mon": "Понедельник",
    "Tue": "Вторник",
    "Wed": "Среда",
    "Thu": "Четверг",
    "Fri": "Пятница",
    "Sat": "Суббота",
    "Sun": "Воскресенье",
}

months = {
    "Jan": "Января",
    "Feb": "Февраля",
    "Mar": "Марта",
    "Apr": "Апреля",
    "May": "Мая",
    "Jun": "Июня",
    "Jul": "Июля",
    "Aug": "Августа",
    "Sep": "Сентября",
    "Oct": "Октября",
    "Nov": "Ноября",
    "Dec": "Декабря",
}


def decode_email_subject(encoded_subject):
    try:
        # Extract the base64-encoded part
        start_index = encoded_subject.find("?B?") + 3
        end_index = encoded_subject.rfind("?=")
        encoded_subject = encoded_subject[start_index:end_index]

        # Decode the base64 string
        decoded_subject = base64.b64decode(encoded_subject)
        decoded_subject = decoded_subject.decode('utf-8')

        return decoded_subject

    except (base64.binascii.Error, UnicodeDecodeError) as e:
        # Handle decoding errors
        return None


def convert_date(date_string: str):
    # Extract the time zone information in parentheses, if present
    match = re.search(r'\((\w+)\)$', date_string)
    time_zone = match.group(1) if match else None

    # Remove the time zone information from the date string
    date_string_without_timezone = re.sub(r'\s*\(\w+\)$', '', date_string)

    # Convert GMT to UTC for compatibility with %z format
    date_string_without_timezone = re.sub(r'GMT$', '+0000', date_string_without_timezone)

    # Parse the date string without the time zone
    date_object = datetime.strptime(date_string_without_timezone, "%a, %d %b %Y %H:%M:%S %z")

    # Format the parsed date with the time zone information
    formatted_date = "{}, {} {} {} {:02}:{:02}:{:02}".format(
        days_of_week[date_object.strftime("%a")],
        date_object.day,
        months[date_object.strftime("%b")],
        date_object.year,
        date_object.hour,
        date_object.minute,
        date_object.second
    )

    # Add the time zone information if available
    if time_zone:
        formatted_date += f" {time_zone}"

    return formatted_date


def decode_email_header(header):
    # Декодируем заголовок
    decoded_parts = email.header.decode_header(header)
    decoded_string = ""
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            decoded_string += part.decode(encoding or 'utf-8', errors='replace')
        elif isinstance(part, str):
            decoded_string += part

    # Заменяем < и > на "
    decoded_string = decoded_string.replace('<', ' ').replace('>', ' ')

    return decoded_string


def decode_email_subject(subject):
    decoded_parts = email.header.decode_header(subject)
    decoded_subject = ""
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            decoded_subject += part.decode(encoding or 'utf-8', errors='replace')
        elif isinstance(part, str):
            decoded_subject += part
    return decoded_subject


def decode_email_body(email_message):
    text_body = ""

    if email_message.is_multipart():
        for part in email_message.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if "attachment" not in content_disposition:
                text_body += decode_email_body(part)
    else:
        content_type = email_message.get_content_type()
        text = email_message.get_payload(decode=True)

        if "text" in content_type:
            charset = email_message.get_content_charset() or "utf-8"
            try:
                text = text.decode(charset, errors='replace')
            except UnicodeDecodeError:
                text = str(text, errors='replace')

            # Конвертация HTML в текст
            if "html" in content_type:
                text = html2text.html2text(text)

            text_body += text

    return text_body


def check_format_password(input_string):
    # Паттерн для проверки формата
    pattern = re.compile(r'^[a-z]+\s[a-z]+\s[a-z]+\s[a-z]+$')

    # Проверка соответствия строки паттерну
    if re.match(pattern, input_string):
        return True
    else:
        return False


# Функция для подключения к почте
def connect_to_mail_class(my_mail):
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(my_mail.mail, my_mail.hashed_password)
    return mail


def connect_to_mail_dict(credentials):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(credentials['mail'], credentials['hashed_password'])
        return mail
    except imaplib.IMAP4.error as e:
        error_message = str(e)
        if "Invalid credentials" in error_message:
            return "LoginFatal"
        else:
            return f"Error connecting to mail: {error_message}"


def validate_and_normalize_email(mail: str):
    try:
        v = validate_email(mail)
        normal_mail = v.normalized
        return normal_mail
    except EmailNotValidError:
        return None


def format_email_list(emails, start_index=1):
    formatted_emails = "\n".join([f"{i}) {mail}" for i, mail in enumerate(emails, start=start_index)])
    return formatted_emails


async def send_whitelist_page(page, message, whitelist, start_index=1, max_emails_per_page=10):
    current_start_index = (page - 1) * max_emails_per_page + start_index
    end_index = current_start_index + max_emails_per_page - 1

    page_emails = whitelist[current_start_index-1:end_index]

    formatted_emails = format_email_list(page_emails, start_index=current_start_index)
    total_pages = (len(whitelist) + max_emails_per_page - 1) // max_emails_per_page

    keyboard = []

    if page > 1:
        keyboard.append([InlineKeyboardButton(text="Предыдущая страница⬅", callback_data=f"whitelist_prev_page"
                                                                                         f"_{page}")])

    if page < total_pages:
        keyboard.append([InlineKeyboardButton(text="Следующая страница➡", callback_data=f"whitelist_next_page_{page}")])

    keyboard_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await message.answer(f"✅Белый список ({page}/{total_pages})✅\n\n{formatted_emails}",
                           reply_markup=keyboard_markup)
    await message.delete()
