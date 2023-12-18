import imaplib
import email
import time
import base64
from datetime import datetime
from bs4 import BeautifulSoup

days_of_week = {
    'Mon': 'Понедельник',
    'Tue': 'Вторник',
    'Wed': 'Среда',
    'Thu': 'Четверг',
    'Fri': 'Пятница',
    'Sat': 'Суббота',
    'Sun': 'Воскресенье'
}

months = {
    'Jan': 'Января',
    'Feb': 'Февраля',
    'Mar': 'Марта',
    'Apr': 'Апреля',
    'May': 'Мая',
    'Jun': 'Июня',
    'Jul': 'Июля',
    'Aug': 'Августа',
    'Sep': 'Сентября',
    'Oct': 'Октября',
    'Nov': 'Ноября',
    'Dec': 'Декабря'
}

# credentials
username = "alexandrzarudnev57@gmail.com"

# generated app password
app_password = "ksqk uuwe tpuf lljx"

# https://www.systoolsgroup.com/imap/
gmail_host = 'imap.gmail.com'

# Переменная для хранения UID последнего обработанного сообщения
last_processed_uid = None

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


while True:
    try:
        # set connection
        mail = imaplib.IMAP4_SSL(gmail_host)

        # login
        mail.login(username, app_password)

        # select inbox
        mail.select("INBOX")

        # search for all mails
        _, message_numbers = mail.search(None, 'ALL')

        # получение списка UID сообщений
        uids = message_numbers[0].split()

        # Определение последнего UID, если есть сообщения
        if uids:
            latest_uid = uids[-1]

            # Если это первый запуск или есть новые сообщения
            if last_processed_uid is None or latest_uid != last_processed_uid:
                # fetch the latest message
                _, data = mail.fetch(latest_uid, '(RFC822)')
                _, bytes_data = data[0]

                # convert the byte data to message
                email_message = email.message_from_bytes(bytes_data)

                # access data
                print("\n===========================================")
                print("Subject: ", decode_email_subject(email_message["subject"]))
                print("To:", email_message["to"])
                print("From: ", decode_email_subject(email_message["from"].split(" ")[0]) + " " + email_message["from"].split(" ")[1])
                print("Date: ", convert_date(email_message["date"]))
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain" or part.get_content_type() == "text/html":
                        message = part.get_payload(decode=True)
                        print("Message: ", BeautifulSoup(message.decode(), "html.parser").get_text())
                        print("==========================================\n")

                # Обновление переменной last_processed_uid
                last_processed_uid = latest_uid

        # close the connection
        mail.close()
        mail.logout()

    except Exception as e:
        print(f"An error occurred: {e}")

    # Пауза между проверками (например, каждые 60 секунд)
    time.sleep(5)
