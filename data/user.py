import sqlalchemy as db
from .db_session import SqlAlchemyBase
from sqlalchemy import orm

from flask_login import UserMixin

from datetime import datetime


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, index=True)
    login = db.Column(db.String(32), nullable=False, unique=True, index=True)
    email = db.Column(db.String(64), nullable=True, unique=True, index=True)
    name = db.Column(db.String(32), nullable=False)
    surname = db.Column(db.String(32), nullable=False)
    patronymic = db.Column(db.String(32), nullable=True)
    hashed_password = db.Column(db.String, nullable=False)
    about = db.Column(db.String, nullable=True, default="")
    is_admin = db.Column(db.Boolean, default=False)
    is_teacher = db.Column(db.Boolean, default=False)
    is_news_publisher = db.Column(db.Boolean, default=False)
    # group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=True, index=True, default=None)
    creation_date = db.Column(db.DateTime, default=datetime.now)
    last_auth = db.Column(db.DateTime, default=datetime.now)
    avatar = db.Column(db.String, default=None)
    is_from_proton = db.Column(db.Boolean, default=False)
    posts_only_for_friends = db.Column(db.Boolean, default=False)
    talk_only_with_friends = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, nullable=False, default=False)
    ban_reason = db.Column(db.String, nullable=True, default=None)
    friends = db.Column(db.String, nullable=False, default="")
    friends_num = db.Column(db.Integer, nullable=False, default=0)
    friends_req = db.Column(db.String, nullable=False, default="")

    posts = orm.relation("Post", back_populates="user")
    news = orm.relation("News", back_populates="user")
    messages = orm.relation("Message", back_populates="user")
    # group = orm.relation("Group", back_populates='users')
    # balance = orm.relation("Balance", back_populates='user', uselist=False)
    # orders = orm.relation("Order", back_populates='user')