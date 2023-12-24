from sqlalchemy.orm import Session
from sqlalchemy import select

from . import get_db
from .models import User, ConnectedMail


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


async def add_connected_email(mail: str, password: str, user_id: int):
    async for db in get_db():
        existing_connected_mail = await db.execute(
            select(ConnectedMail).join(User).filter(ConnectedMail.user_id == User.telegram_id)
        )
        existing_connected_mail = existing_connected_mail.first()

        if not existing_connected_mail:
            new_connected_mail = ConnectedMail(mail=mail, hashed_password=password, user_id=user_id)
            db.add(new_connected_mail)
            await db.commit()
            return "Почта успешно добавлена👏"
        else:
            return "У вас уже есть привязанная почта😕"


async def get_my_connected_mail(user_id: int):
    async for db in get_db():
        connected_mail = await db.execute(
            select(ConnectedMail).where(ConnectedMail.user_id == user_id)
        )
        connected_mail = connected_mail.first()

        if not connected_mail:
            return False
        return connected_mail
