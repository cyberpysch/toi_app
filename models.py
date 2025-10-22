# app/models.py
from sqlalchemy import Column, Integer, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base
import datetime

Base = declarative_base()

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    url = Column(Text, unique=True, nullable=False)
    title = Column(Text, nullable=False)
    summary = Column(Text)
    facts = Column(JSONB)
    mcqs = Column(JSONB)
    timestamp = Column(TIMESTAMP, default=datetime.datetime.utcnow)
    article_img = Column(Text)
