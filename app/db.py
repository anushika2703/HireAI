import json
import sqlite3
from contextlib import contextmanager

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL, company TEXT DEFAULT '', location TEXT DEFAULT '',
  description TEXT NOT NULL,
  required TEXT NOT NULL, nice TEXT NOT NULL DEFAULT '[]',
  min_years REAL DEFAULT 0, max_years REAL DEFAULT 99
);
CREATE TABLE IF NOT EXISTS candidates(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  resume_text TEXT NOT NULL, profile TEXT NOT NULL
);
"""


@contextmanager
def conn():
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(config.DB_PATH)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def _job(r) -> dict:
    d = dict(r)
    d["required"] = json.loads(d["required"])
    d["nice"] = json.loads(d["nice"])
    return d


def init_db() -> None:
    with conn() as c:
        c.executescript(SCHEMA)
        if c.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 0:
            for j in json.loads((config.SEED_DIR / "jobs.json").read_text()):
                _insert(c, j)


def _insert(c, j: dict) -> int:
    cur = c.execute(
        "INSERT INTO jobs(title,company,location,description,required,nice,min_years,max_years)"
        " VALUES(?,?,?,?,?,?,?,?)",
        (j["title"], j.get("company", ""), j.get("location", ""), j["description"],
         json.dumps(j["required"]), json.dumps(j.get("nice", [])),
         j.get("min_years", 0), j.get("max_years", 99)),
    )
    return cur.lastrowid


def all_jobs() -> list[dict]:
    with conn() as c:
        return [_job(r) for r in c.execute("SELECT * FROM jobs ORDER BY id")]


def add_job(j: dict) -> int:
    with conn() as c:
        return _insert(c, j)


def save_candidate(text: str, profile: dict) -> int:
    with conn() as c:
        return c.execute("INSERT INTO candidates(resume_text, profile) VALUES(?,?)",
                         (text, json.dumps(profile))).lastrowid


def get_candidate(cid: int) -> dict | None:
    with conn() as c:
        r = c.execute("SELECT * FROM candidates WHERE id=?", (cid,)).fetchone()
    if not r:
        return None
    return {"id": r["id"], "resume_text": r["resume_text"], "profile": json.loads(r["profile"])}
