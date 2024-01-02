from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload

from . import get_db
from .models import User, ConnectedMail, Mail, Whitelist


async def get_user_by_id(user_id: int):
    async for db in get_db():
        existing_user = await db.execute(
            select(User).where(User.telegram_id == user_id)
        )
        existing_user = existing_user.first()
        return existing_user


async def add_user(user_id: int):
    async for db in get_db():
        existing_user = await db.execute(
            select(User).where(User.telegram_id == user_id)
        )
        existing_user = existing_user.first()

        if not existing_user:
            new_user = User(telegram_id=user_id)
            db.add(new_user)
            await db.commit()
            return "Никогда не пользовались нашим ботом? Сейчас все покажем."
        else:
            return "Рады видеть старых друзей."


async def get_my_connected_mail(user_id: int):
    async for db in get_db():
        connected_mail = await db.execute(
            select(ConnectedMail).where(ConnectedMail.user_id == user_id)
        )
        connected_mail = connected_mail.first()

        if connected_mail is not None:
            return connected_mail  # Возвращаем объект connected_mail, если он существует

    return None


async def add_connected_email(mail: str, password: str, user_id: int):
    async for db in get_db():
        existing_connected_mail = await get_my_connected_mail(user_id)

        if not existing_connected_mail:
            new_connected_mail = ConnectedMail(mail=mail, hashed_password=password, user_id=user_id)
            db.add(new_connected_mail)
            await db.commit()
            return "Почта успешно добавлена👏"
        else:
            return "У вас уже есть привязанная почта😕"


async def add_mail_to_white_list(mail: str, user_id: int):
    async for db in get_db():
        # Проверяем существует ли email
        existing_mail = await db.execute(
            select(Mail).where(Mail.mail == mail)
        )
        existing_mail = existing_mail.first()

        if existing_mail is None:
            # Если email не существует, создаем новый
            new_mail = Mail(mail=mail)
            db.add(new_mail)
            await db.commit()
        else:
            # Если email существует, используем его
            new_mail = existing_mail[0]

        # Проверяем, существует ли уже запись в whitelist
        existing_whitelist_entry = await db.execute(
            select(Whitelist).where(
                and_(Whitelist.user_id == user_id, Whitelist.mail_id == new_mail.id)
            )
        )
        existing_whitelist_entry = existing_whitelist_entry.first()

        if existing_whitelist_entry:
            return 409  # Конфликт, запись уже существует

        # Добавляем запись в whitelist
        new_mail_in_whitelist = Whitelist(user_id=user_id, mail_id=new_mail.id)
        db.add(new_mail_in_whitelist)
        await db.commit()

        return 201  # Успешно добавлено в whitelist


async def get_white_list(user_id: int):
    async for db in get_db():
        white_list = await db.execute(
            select(Mail).join(Whitelist).where(Whitelist.user_id == user_id)
        )
        white_list = white_list.scalars().all()
        return [mail.mail for mail in white_list]





