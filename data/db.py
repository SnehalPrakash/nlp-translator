"""SQLite Database Manager for:
1. SHA-256 Translation Cache (sub-millisecond repeat hits)
2. Translation History & Starred Favorites
3. Offline English-Pivot Lexicon (Definitions, Synonyms, Antonyms)
"""

import hashlib
import os
import sqlite3
import time
from typing import Any, Dict, List, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "translator.db")


def get_db_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Translation Cache table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS translation_cache (
            hash TEXT PRIMARY KEY,
            source_text TEXT NOT NULL,
            translated_text TEXT NOT NULL,
            src_lang TEXT NOT NULL,
            tgt_lang TEXT NOT NULL,
            hit_count INTEGER DEFAULT 1,
            created_at REAL NOT NULL,
            last_accessed REAL NOT NULL
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_cache_lookup ON translation_cache(hash)")

    # 2. History table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_text TEXT NOT NULL,
            translated_text TEXT NOT NULL,
            src_lang TEXT NOT NULL,
            tgt_lang TEXT NOT NULL,
            is_favorite INTEGER DEFAULT 0,
            created_at REAL NOT NULL
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_history_created ON history(created_at DESC)")

    # 3. Lexicon table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lexicon (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL UNIQUE,
            pos TEXT,
            definition TEXT,
            synonyms TEXT,
            antonyms TEXT,
            examples TEXT
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_lexicon_word ON lexicon(word)")

    conn.commit()
    conn.close()


def compute_hash(text: str, src_lang: str, tgt_lang: str) -> str:
    norm = text.strip().lower()
    payload = f"{norm}:{src_lang.lower()}:{tgt_lang.lower()}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class CacheService:
    @staticmethod
    def get(text: str, src_lang: str, tgt_lang: str) -> Optional[str]:
        h = compute_hash(text, src_lang, tgt_lang)
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT translated_text FROM translation_cache WHERE hash = ?", (h,))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE translation_cache SET hit_count = hit_count + 1, last_accessed = ? WHERE hash = ?", (time.time(), h))
            conn.commit()
            conn.close()
            return row["translated_text"]
        conn.close()
        return None

    @staticmethod
    def set(text: str, translated: str, src_lang: str, tgt_lang: str):
        h = compute_hash(text, src_lang, tgt_lang)
        conn = get_db_connection()
        cur = conn.cursor()
        now = time.time()
        cur.execute("""
            INSERT INTO translation_cache (hash, source_text, translated_text, src_lang, tgt_lang, hit_count, created_at, last_accessed)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?)
            ON CONFLICT(hash) DO UPDATE SET
                translated_text = excluded.translated_text,
                hit_count = translation_cache.hit_count + 1,
                last_accessed = excluded.last_accessed
        """, (h, text, translated, src_lang, tgt_lang, now, now))
        conn.commit()
        conn.close()


class HistoryService:
    @staticmethod
    def add(source_text: str, translated_text: str, src_lang: str, tgt_lang: str) -> int:
        conn = get_db_connection()
        cur = conn.cursor()
        now = time.time()
        cur.execute("""
            INSERT INTO history (source_text, translated_text, src_lang, tgt_lang, is_favorite, created_at)
            VALUES (?, ?, ?, ?, 0, ?)
        """, (source_text, translated_text, src_lang, tgt_lang, now))
        rec_id = cur.lastrowid
        conn.commit()
        conn.close()
        return rec_id

    @staticmethod
    def list_recent(limit: int = 50) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, source_text, translated_text, src_lang, tgt_lang, is_favorite, created_at
            FROM history
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def toggle_favorite(record_id: int) -> bool:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE history SET is_favorite = 1 - is_favorite WHERE id = ?", (record_id,))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def clear():
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM history")
        conn.commit()
        conn.close()


class LexiconService:
    @staticmethod
    def lookup(word: str) -> Optional[Dict[str, Any]]:
        cleaned = word.strip().lower()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT word, pos, definition, synonyms, antonyms, examples
            FROM lexicon
            WHERE word = ?
        """, (cleaned,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        res = dict(row)
        # Parse comma-separated fields
        res["synonyms"] = [s.strip() for s in (res["synonyms"] or "").split(",") if s.strip()]
        res["antonyms"] = [a.strip() for a in (res["antonyms"] or "").split(",") if a.strip()]
        res["examples"] = [e.strip() for e in (res["examples"] or "").split(";") if e.strip()]
        return res

    @staticmethod
    def seed_initial():
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as count FROM lexicon")
        if cur.fetchone()["count"] > 0:
            conn.close()
            return

        # Seed initial rich lexicon for demonstration and testing
        starter_words = [
            ("hello", "interjection", "An expression of greeting or beginning a conversation.", "hi, greetings, welcome", "goodbye, farewell", "Hello, how are you today?;She called to say hello."),
            ("friend", "noun", "A person with whom one has a bond of mutual affection.", "companion, pal, comrade, ally", "enemy, adversary, foe", "A friend in need is a friend indeed.;He went to dinner with a friend."),
            ("water", "noun", "A transparent, odorless, tasteless liquid essential for life.", "aqua, liquid, moisture", "fire, drought", "Please drink plenty of water.;Water flows down the hill."),
            ("love", "noun / verb", "An intense feeling of deep affection; to feel love for.", "affection, devotion, fondness", "hatred, enmity, dislike", "Love conquers all.;They love spending time together."),
            ("book", "noun", "A written or printed work consisting of pages bound together.", "volume, publication, tome", "—", "He is reading a fascinating book.;Knowledge is found in books."),
            ("good", "adjective", "To be desired or approved of; having high quality.", "fine, excellent, great, pleasant", "bad, poor, terrible", "Have a good day!;She did a good job on the project."),
            ("peace", "noun", "Freedom from disturbance; tranquility and harmony.", "calm, serenity, harmony, quiet", "war, conflict, chaos", "Let there be peace on earth.;He sought inner peace in nature."),
            ("knowledge", "noun", "Facts, information, and skills acquired through experience or education.", "wisdom, insight, learning, comprehension", "ignorance, inexperience", "Knowledge is power.;She has a vast knowledge of history."),
            ("home", "noun", "The place where one lives permanently, especially as a member of a family or household.", "abode, residence, dwelling, sanctuary", "away, foreign", "There is no place like home.;He returned home after a long journey."),
            ("beautiful", "adjective", "Pleasing the senses or mind aesthetically.", "gorgeous, lovely, stunning, attractive", "ugly, repulsive, hideous", "It was a beautiful sunrise.;She has a beautiful voice."),
        ]

        cur.executemany("""
            INSERT OR IGNORE INTO lexicon (word, pos, definition, synonyms, antonyms, examples)
            VALUES (?, ?, ?, ?, ?, ?)
        """, starter_words)
        conn.commit()
        conn.close()


# Initialize database on module load
init_db()
LexiconService.seed_initial()
