# main.py
import os
import json
import time
import logging
import queue
import threading
import random
from datetime import datetime
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import OperationalError, SQLAlchemyError

# local imports
from database import SessionLocal, engine
from models import Article, Base

# Setup
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("toi-scraper")

# Ensure table exists
Base.metadata.create_all(bind=engine)

# OpenAI client
client = OpenAI(api_key="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")

# Scraper settings
BASE_DOMAIN = "https://timesofindia.indiatimes.com"
SECTIONS = ["BUSINESS", "EDUCATION", "SCIENCE", "WORLD", "NATION", "TECH"]
START_PAGE = 1
END_PAGE = 2

RAW_PATH = "data/raw_articles/"
os.makedirs(RAW_PATH, exist_ok=True)

# High-throughput queue & batch settings
QUEUE_MAXSIZE = 10000
ARTICLE_QUEUE = queue.Queue(maxsize=QUEUE_MAXSIZE)

BATCH_SIZE = int(os.getenv("DB_BATCH_SIZE", 25))     # number of rows to write per DB transaction
BATCH_TIMEOUT = int(os.getenv("DB_BATCH_TIMEOUT", 3))  # seconds max to wait before flushing batch

# Retry policy for DB actions (tenacity)
retry_db = retry(
    reraise=True,
    stop=stop_after_attempt(6),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((OperationalError, SQLAlchemyError))
)

# Utility: get article listing links
def get_article_links(section, page_number):
    url = f"{BASE_DOMAIN}/{section}?page={page_number}"
    try:
        resp = requests.get(url, timeout=10, verify=False)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "articleshow" in href:
                full = href if href.startswith("http") else BASE_DOMAIN + href.split("?")[0]
                links.append(full.split("?")[0])
        return list(set(links))
    except Exception as e:
        logger.exception("Failed to fetch listing %s page %s: %s", section, page_number, e)
        return []

# Extract content (same selectors you used)
def extract_article(url):
    try:
        resp = requests.get(url, timeout=10, verify=False)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        title_tag = soup.find("title")
        title = title_tag.get_text().strip() if title_tag else "Untitled Article"
        img_nodes = soup.select("div.wJnIp")
        img_link = None
        for div in img_nodes:
            img = div.find("img")
            if img and img.get("src"):
                img_link = img["src"]
                break
        para_nodes = soup.select("div._s30J.clearfix")
        content_parts = [p.get_text(strip=True) for p in para_nodes]
        content = " ".join(content_parts)
        return {"url": url, "title": title, "content": content, "img": img_link}
    except Exception as e:
        logger.exception("Error extracting article %s: %s", url, e)
        return None

# Simple AI filter - keep as is (may be rate-limited in prod)
def is_current_affairs(article_text):
    try:
        prompt = f"""
        Decide if the following article is about current affairs, politics, world news, or economy.
        Answer with YES or NO only.
        Article: {article_text[:1000]}
        """
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":prompt}],
            temperature=0
        )
        answer = response.choices[0].message.content.strip().upper()
        return answer == "YES"
    except Exception as e:
        logger.exception("AI relevance check failed: %s", e)
        # fail-safe: treat uncertain as False
        return False

# Generate structured output using your prompt file
def generate_structured_output(article_text):
    try:
        prompt_file = os.path.join("prompts", "summary_prompt.json")
        with open(prompt_file, "r", encoding="utf-8") as f:
            system_prompt = json.load(f)["content"]
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":system_prompt}, {"role":"user","content":article_text}],
            temperature=0.3
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.exception("AI generate structured failed: %s", e)
        return {"summary": "", "key_facts": [], "possible_questions": []}

# Producer: find pages and push extracted article dicts into ARTICLE_QUEUE
def producer_loop(stop_event):
    """Continuously scans sections and pushes articles into the queue."""
    while not stop_event.is_set():
        try:
            for section in SECTIONS:
                for page in range(START_PAGE, END_PAGE + 1):
                    links = get_article_links(section, page)
                    if not links:
                        continue
                    # you can randomize to reduce predictable load
                    random.shuffle(links)
                    for url in links:
                        if stop_event.is_set():
                            break
                        article = extract_article(url)
                        if not article or len(article.get("content","")) < 500:
                            logger.debug("Skipping short/invalid article: %s", url)
                            continue
                        if not is_current_affairs(article["content"]):
                            logger.debug("Non current-affairs: %s", article["title"])
                            continue
                        ai_output = generate_structured_output(article["content"])
                        item = {
                            "url": article["url"],
                            "title": article["title"],
                            "summary": ai_output.get("summary",""),
                            "facts": ai_output.get("key_facts", []),
                            "mcqs": ai_output.get("possible_questions", []),
                            "timestamp": datetime.utcnow(),
                            "article_img": article.get("img")
                        }
                        # Save raw article to disk (optional)
                        safe_title = article['title'][:40].replace(' ','_').replace(':','').replace('?','').replace("'", "")
                        raw_file = os.path.join("data","raw_articles", f"{safe_title}.txt")
                        try:
                            with open(raw_file, "w", encoding="utf-8") as rf:
                                rf.write(article["content"])
                        except Exception:
                            logger.debug("Could not write raw file for %s", safe_title)
                        # Push to queue (block briefly if queue full)
                        while not stop_event.is_set():
                            try:
                                ARTICLE_QUEUE.put(item, timeout=1)
                                break
                            except queue.Full:
                                logger.warning("Queue full; producer waiting to put item...")
                        logger.info("Produced article -> queue: %s", item["url"])
                        # small pause to avoid tight loop, but you may tune this
                        time.sleep(float(os.getenv("PRODUCER_SLEEP", 0.2)))
                    if stop_event.is_set():
                        break
            # After scanning all sections/pages, sleep before next round (reduce load)
            time.sleep(random.randint(30, 90))
        except Exception:
            logger.exception("Producer encountered an error; sleeping briefly and continuing.")
            time.sleep(5)

# DB batch worker
@retry_db
def _insert_batch(session, rows):
    """Perform a single batch upsert; uses pg ON CONFLICT DO NOTHING to avoid duplicates."""
    if not rows:
        return 0
    stmt = pg_insert(Article).values(rows)
    stmt = stmt.on_conflict_do_nothing(index_elements=["url"])
    session.execute(stmt)
    session.commit()
    return len(rows)

def db_worker_loop(stop_event):
    """Consume items from ARTICLE_QUEUE and write to DB in batches."""
    buffer = []
    last_flush = time.time()
    session = None
    try:
        session = SessionLocal()
        while not stop_event.is_set():
            timeout = max(0.0, BATCH_TIMEOUT - (time.time() - last_flush))
            try:
                item = ARTICLE_QUEUE.get(timeout=timeout if timeout > 0 else 0.5)
                buffer.append(item)
                ARTICLE_QUEUE.task_done()
            except queue.Empty:
                pass

            # flush if buffer reached size or timeout expired
            if len(buffer) >= BATCH_SIZE or (buffer and (time.time() - last_flush) >= BATCH_TIMEOUT):
                try:
                    logger.info("Flushing %d rows to DB...", len(buffer))
                    # Convert timestamp to datetime if isoformat string
                    for r in buffer:
                        if isinstance(r.get("timestamp"), str):
                            r["timestamp"] = datetime.fromisoformat(r["timestamp"])
                    _insert_batch(session, buffer)
                    buffer.clear()
                    last_flush = time.time()
                except Exception:
                    logger.exception("DB worker failed to insert batch; will retry after backoff.")
                    # session may be in bad state; close and recreate session for next attempt
                    try:
                        session.rollback()
                    except Exception:
                        pass
                    try:
                        session.close()
                    except Exception:
                        pass
                    session = SessionLocal()
                    # on exception, we'll continue loop and retry next flush via tenacity decorator
            # small sleep to yield thread
            time.sleep(0.01)
    finally:
        # flush any remaining synchronously before exiting
        if buffer:
            try:
                logger.info("Final flush of %d rows to DB before shutdown...", len(buffer))
                _insert_batch(session or SessionLocal(), buffer)
            except Exception:
                logger.exception("Failed final DB flush.")
        if session:
            session.close()

# Graceful shutdown helper
def run_forever():
    stop_event = threading.Event()
    producer = threading.Thread(target=producer_loop, args=(stop_event,), daemon=True, name="producer-thread")
    db_worker = threading.Thread(target=db_worker_loop, args=(stop_event,), daemon=True, name="db-worker-thread")

    logger.info("Starting producer and db worker threads...")
    producer.start()
    db_worker.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutdown requested (KeyboardInterrupt). Stopping threads...")
        stop_event.set()
        producer.join(timeout=10)
        db_worker.join(timeout=30)
        logger.info("Shutdown complete.")

if __name__ == "__main__":
    run_forever()
