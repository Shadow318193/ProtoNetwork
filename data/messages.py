import sqlalchemy as db
from .db_session import SqlAlchemyBase
from sqlalchemy import orm

from datetime import datetime


class Message(SqlAlchemyBase):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, index=True)
    from_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    to_id = db.Column(db.Integer, nullable=False)
    text = db.Column(db.String, nullable=True, default="")
    media = db.Column(db.String, nullable=True)
    media_type = db.Column(db.String, nullable=True)
    creation_date = db.Column(db.DateTime, default=datetime.now)

    user = orm.relation("User")
    # balance = orm.relation("Balance", back_populates='user', uselist=False)
    # orders = orm.relation("Order", back_populates='user')