from flask import Blueprint, render_template
from sqlalchemy.orm import Session
from database import SessionLocal
from crud import get_all_articles

main_bp = Blueprint('main', __name__)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@main_bp.route("/")
def home():
    db_session = next(get_db())
    articles = get_all_articles(db_session, limit=20)  # latest 20 articles
    return render_template("index.html", articles=articles)
