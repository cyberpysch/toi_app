from sqlalchemy.orm import Session
from models import Article

def get_all_articles(db: Session, limit: int = 100):
    return db.query(Article).order_by(Article.timestamp.desc()).limit(limit).all()

def get_article_by_id(db: Session, article_id: int):
    return db.query(Article).filter(Article.id == article_id).first()

def get_article_by_url(db: Session, url: str):
    return db.query(Article).filter(Article.url == url).first()
