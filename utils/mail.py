import base64
import email
from datetime import datetime
import re
from email.header import decode_header
import html2text
from bs4 import BeautifulSoup

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
        print("An error occurred:", e)
        return None


def convert_date(date_string: str):
    date_object = datetime.strptime(date_string, "%a, %d %b %Y %H:%M:%S %z")
    formatted_date = "{}, {} {} {} {:02}:{:02}:{:02}".format(
        days_of_week[date_object.strftime("%a")],
        date_object.day,
        months[date_object.strftime("%b")],
        date_object.year,
        date_object.hour,
        date_object.minute,
        date_object.second
    )
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


