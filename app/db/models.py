from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    Boolean,
)
from .database import Base


class User(Base):
    __tablename__ = "users"

    telegram_id = Column(Integer, primary_key=True, autoincrement=False, index=True)


class ConnectedMail(Base):
    __tablename__ = "connected_mails"

    id = Column(Integer, primary_key=True, index=True)
    mail = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_launched = Column(Boolean, default=False)
    is_whitelist_active = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.telegram_id"))


class Mail(Base):
    __tablename__ = "mails"

    id = Column(Integer, primary_key=True, index=True)
    mail = Column(String, nullable=False)


class Whitelist(Base):
    __tablename__ = "whitelists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.telegram_id"))
    mail_id = Column(Integer, ForeignKey("mails.id"))
