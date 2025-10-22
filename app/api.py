from flask import Flask, jsonify, request
from sqlalchemy.orm import Session
from database import SessionLocal
from crud import get_all_articles, get_article_by_id

app = Flask(__name__)

# Dependency: get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# GET /articles?limit=50
@app.route("/articles", methods=["GET"])
def read_articles():
    limit = request.args.get("limit", default=50, type=int)
    db_session = next(get_db())
    articles = get_all_articles(db_session, limit=limit)
    result = []
    for a in articles:
        result.append({
            "id": a.id,
            "url": a.url,
            "title": a.title,
            "summary": a.summary,
            "facts": a.facts,
            "mcqs": a.mcqs,
            "timestamp": a.timestamp.isoformat(),
            "article_img": a.article_img
        })
    return jsonify(result)

# GET /articles/<id>
@app.route("/articles/<int:article_id>", methods=["GET"])
def read_article(article_id):
    db_session = next(get_db())
    article = get_article_by_id(db_session, article_id)
    if article is None:
        return jsonify({"error": "Article not found"}), 404
    return jsonify({
        "id": article.id,
        "url": article.url,
        "title": article.title,
        "summary": article.summary,
        "facts": article.facts,
        "mcqs": article.mcqs,
        "timestamp": article.timestamp.isoformat(),
        "article_img": article.article_img
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
