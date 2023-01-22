import sqlalchemy as db
from .db_session import SqlAlchemyBase
from sqlalchemy import orm

from datetime import datetime


class Post(SqlAlchemyBase):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, index=True)
    poster_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    text = db.Column(db.String, nullable=True, default="")
    likes = db.Column(db.Integer, nullable=False, default=0)
    who_liked = db.Column(db.String, nullable=False, default="")
    media = db.Column(db.String, nullable=True)
    media_type = db.Column(db.String, nullable=True)
    creation_date = db.Column(db.DateTime, default=datetime.now)
    parent_post = db.Column(db.Integer, nullable=True, default=None)

    user = orm.relation("User")
    # balance = orm.relation("Balance", back_populates='user', uselist=False)
    # orders = orm.relation("Order", back_populates='user')