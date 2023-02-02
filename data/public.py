import sqlalchemy as db
from .db_session import SqlAlchemyBase
from sqlalchemy import orm

from datetime import datetime


class Public(SqlAlchemyBase):
    __tablename__ = 'publics'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, index=True)
    name = db.Column(db.String, nullable=False)
    about = db.Column(db.String, nullable=True, default="")
    creation_date = db.Column(db.DateTime, default=datetime.now)
    avatar = db.Column(db.String, default=None)
    is_banned = db.Column(db.Boolean, nullable=False, default=False)
    ban_reason = db.Column(db.String, nullable=True, default=None)
    subscribers = db.Column(db.Integer, default=0, nullable=False)
    who_subscribed = db.Column(db.String, default="", nullable=False)
    admins = db.Column(db.String, default="", nullable=False)
    moderators = db.Column(db.String, default="", nullable=False)

    posts = orm.relation("Post", back_populates="public")
