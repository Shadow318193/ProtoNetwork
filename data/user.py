import sqlalchemy as db
from .db_session import SqlAlchemyBase
from sqlalchemy import orm

from flask_login import UserMixin
from datetime import datetime
from uuid import uuid4


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
    # group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=True, index=True)
    creation_date = db.Column(db.DateTime, default=datetime.now)
    last_auth = db.Column(db.DateTime, default=None, nullable=True)
    avatar = db.Column(db.String(128), default=None)
    is_from_proton = db.Column(db.Boolean, default=False)

    # group = orm.relation("Group", back_populates='users')
    # balance = orm.relation("Balance", back_populates='user', uselist=False)
    # orders = orm.relation("Order", back_populates='user')