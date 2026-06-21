#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEUTSCH MEISTER PRO - SQLite Ma'lumotlar Bazasi
To'liq yangilangan versiya - Barcha jadvallar bilan
"""

import sqlite3
import json
import datetime
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager

from config import logger, DATABASE_PATH, XP_REWARDS


class Database:
    """Asosiy ma'lumotlar bazasi klassi"""

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.init_database()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def init_database(self):
        """Barcha jadvallarni yaratadi"""
        with self._connect() as conn:
            cursor = conn.cursor()

            # 1. Foydalanuvchilar jadvali
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    phone TEXT,
                    current_level TEXT DEFAULT 'a1',
                    target_level TEXT DEFAULT 'c1',
                    total_xp INTEGER DEFAULT 0,
                    streak_days INTEGER DEFAULT 0,
                    last_active TEXT,
                    joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    voice_preference TEXT DEFAULT 'female',
                    tts_speed REAL DEFAULT 1.0,
                    show_mistakes INTEGER DEFAULT 1,
                    ai_difficulty TEXT DEFAULT 'adaptive',
                    speaking_score REAL DEFAULT 0.0,
                    total_conversations INTEGER DEFAULT 0,
                    is_admin INTEGER DEFAULT 0
                )
            """)

            # 2. Xatolar jadvali
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mistakes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    user_input TEXT,
                    correct_form TEXT,
                    mistake_type TEXT,
                    mini_lesson TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TEXT,
                    mastered INTEGER DEFAULT 0,
                    review_count INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # 3. Progress jadvali
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    xp_amount INTEGER,
                    activity_type TEXT,
                    activity_detail TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # 4. Kunlik so'zlar jadvali
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    german TEXT,
                    uzbek TEXT,
                    izoh TEXT,
                    misol TEXT,
                    sinonimlar TEXT,
                    date TEXT,
                    learned INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # 5. Suhbatlar tarixi
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    topic TEXT,
                    messages TEXT,
                    score INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # 6. Admin murojaatlari
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    user_name TEXT,
                    request_type TEXT,
                    message TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TEXT,
                    admin_reply TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # 7. Lug'at kitoblari
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lugat_books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 8. Lug'at bo'limlari
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lugat_chapters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER,
                    name TEXT NOT NULL,
                    description TEXT,
                    order_num INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (book_id) REFERENCES lugat_books(id)
                )
            """)

            # 9. Lug'at so'zlari
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lugat_words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chapter_id INTEGER,
                    german TEXT NOT NULL,
                    uzbek TEXT NOT NULL,
                    izoh TEXT,
                    sinonimlar TEXT,
                    order_num INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chapter_id) REFERENCES lugat_chapters(id)
                )
            """)

            # 10. Sayfa materiallari
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sayfa_materials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_key TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    pdf_path TEXT,
                    audio_path TEXT,
                    order_num INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 11. Kitob materiallari
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS kitob_books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    author TEXT,
                    cover_image TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 12. Kitob materiallari fayllari
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS kitob_materials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER,
                    name TEXT NOT NULL,
                    description TEXT,
                    file_path TEXT NOT NULL,
                    type TEXT DEFAULT 'pdf',
                    order_num INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (book_id) REFERENCES kitob_books(id)
                )
            """)

            # 13. Aktiv Sprechen - Mavzular
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS aktiv_topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    topic_id INTEGER,
                    name_uz TEXT,
                    name_de TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 14. Aktiv Sprechen - Lugatlar
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS aktiv_vocab (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic_id INTEGER,
                    level TEXT,
                    german TEXT NOT NULL,
                    uzbek TEXT NOT NULL,
                    plural TEXT,
                    article TEXT,
                    example_de TEXT,
                    example_uz TEXT,
                    FOREIGN KEY (topic_id) REFERENCES aktiv_topics(id)
                )
            """)

            # 15. Aktiv Sprechen - Hikoyalar
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS aktiv_stories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic_id INTEGER,
                    level TEXT,
                    title_de TEXT,
                    title_uz TEXT,
                    story_de TEXT,
                    story_uz TEXT,
                    grammar_notes TEXT,
                    FOREIGN KEY (topic_id) REFERENCES aktiv_topics(id)
                )
            """)

            # 16. Aktiv Sprechen - Grammatika
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS aktiv_grammar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic_id INTEGER,
                    level TEXT,
                    rule_name TEXT,
                    rule_explanation TEXT,
                    examples TEXT,
                    FOREIGN KEY (topic_id) REFERENCES aktiv_topics(id)
                )
            """)

            # 17. Test natijalari
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    level TEXT,
                    score INTEGER,
                    total_questions INTEGER,
                    correct_answers INTEGER,
                    time_taken INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # 18. Xabar yuborish logi
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS broadcast_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER,
                    message TEXT,
                    recipient_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            logger.info("Barcha jadvallar yaratildi!")

        self._seed_default_data()

    def _seed_default_data(self):
        """Standart ma'lumotlarni kiritish"""
        from config import AKTIV_SPRECHEN_TOPICS

        with self._connect() as conn:
            cursor = conn.cursor()

            # Aktiv Sprechen mavzularini tekshirish
            cursor.execute("SELECT COUNT(*) as c FROM aktiv_topics")
            if cursor.fetchone()["c"] == 0:
                for level, topics in AKTIV_SPRECHEN_TOPICS.items():
                    for topic in topics:
                        cursor.execute(
                            "INSERT INTO aktiv_topics (level, topic_id, name_uz, name_de) VALUES (?, ?, ?, ?)",
                            (level, topic["id"], topic["name"], topic["german"])
                        )
                conn.commit()
                logger.info(f"Aktiv Sprechen: {sum(len(t) for t in AKTIV_SPRECHEN_TOPICS.values())} ta mavzu qo'shildi")

    # ==================== USERS ====================

    def get_or_create_user(self, user_id: int, username=None, first_name=None, last_name=None):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()

            if not user:
                cursor.execute("""
                    INSERT INTO users (user_id, username, first_name, last_name, last_active)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, username, first_name, last_name, datetime.datetime.now().isoformat()))
                conn.commit()
                cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                user = cursor.fetchone()
            else:
                cursor.execute("UPDATE users SET last_active = ? WHERE user_id = ?",
                               (datetime.datetime.now().isoformat(), user_id))
                conn.commit()

            return dict(user) if user else {}

    def update_user(self, user_id: int, **kwargs):
        with self._connect() as conn:
            cursor = conn.cursor()
            for key, value in kwargs.items():
                cursor.execute(f"UPDATE users SET {key} = ? WHERE user_id = ?", (value, user_id))
            conn.commit()

    def get_user(self, user_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else {}

    def get_all_users(self, limit: int = 100, offset: int = 0):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY joined_at DESC LIMIT ? OFFSET ?", (limit, offset))
            return [dict(row) for row in cursor.fetchall()]

    def get_users_count(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM users")
            return cursor.fetchone()["count"]

    def save_phone(self, user_id: int, phone: str):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET phone = ? WHERE user_id = ?", (phone, user_id))
            conn.commit()

    # ==================== XP & PROGRESS ====================

    def add_xp(self, user_id: int, amount: int, activity_type: str, detail: str = ""):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO progress (user_id, xp_amount, activity_type, activity_detail) VALUES (?, ?, ?, ?)",
                           (user_id, amount, activity_type, detail))
            cursor.execute("UPDATE users SET total_xp = total_xp + ? WHERE user_id = ?", (amount, user_id))
            conn.commit()

    def get_total_xp(self, user_id: int) -> int:
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT total_xp FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return row[0] if row else 0

    def get_progress_history(self, user_id: int, limit: int = 50):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM progress WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_level_stats(self):
        """Darajalar bo'yicha statistika"""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT current_level, COUNT(*) as count FROM users GROUP BY current_level")
            return {row["current_level"]: row["count"] for row in cursor.fetchall()}

    # ==================== MISTAKES ====================

    def add_mistake(self, user_id: int, user_input: str, correct_form: str, mistake_type: str):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO mistakes (user_id, user_input, correct_form, mistake_type)
                VALUES (?, ?, ?, ?)
            """, (user_id, user_input, correct_form, mistake_type))
            conn.commit()

    def get_mistakes(self, user_id: int, mastered: bool = False, limit: int = 10):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM mistakes WHERE user_id = ? AND mastered = ? ORDER BY created_at DESC LIMIT ?
            """, (user_id, 1 if mastered else 0, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_mistake_stats(self, user_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM mistakes WHERE user_id = ? AND mastered = 0", (user_id,))
            active = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM mistakes WHERE user_id = ? AND mastered = 1", (user_id,))
            mastered = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM mistakes WHERE user_id = ?", (user_id,))
            total = cursor.fetchone()[0]
            return {"active": active, "mastered": mastered, "total": total}

    def master_mistake(self, mistake_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE mistakes SET mastered = 1, reviewed_at = ? WHERE id = ?",
                           (datetime.datetime.now().isoformat(), mistake_id))
            conn.commit()

    # ==================== DAILY WORDS ====================

    def get_daily_word(self, user_id: int):
        today = datetime.date.today().isoformat()
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM daily_words WHERE user_id = ? AND date = ?", (user_id, today))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def save_daily_word(self, user_id: int, word: dict):
        today = datetime.date.today().isoformat()
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO daily_words (user_id, german, uzbek, izoh, misol, sinonimlar, date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, word.get("german", ""), word.get("uzbek", ""),
                  word.get("izoh", ""), word.get("misol", ""),
                  json.dumps(word.get("sinonimlar", [])), today))
            conn.commit()

    # ==================== ADMIN REQUESTS ====================

    def add_request(self, user_id: int, user_name: str, request_type: str, message: str):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO admin_requests (user_id, user_name, request_type, message)
                VALUES (?, ?, ?, ?)
            """, (user_id, user_name, request_type, message))
            conn.commit()
            return cursor.lastrowid

    def get_requests(self, status: str = None, limit: int = 50):
        with self._connect() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT * FROM admin_requests WHERE status = ? ORDER BY created_at DESC LIMIT ?", (status, limit))
            else:
                cursor.execute("SELECT * FROM admin_requests ORDER BY created_at DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def update_request_status(self, request_id: int, status: str, admin_reply: str = None):
        with self._connect() as conn:
            cursor = conn.cursor()
            if admin_reply:
                cursor.execute("UPDATE admin_requests SET status = ?, resolved_at = ?, admin_reply = ? WHERE id = ?",
                               (status, datetime.datetime.now().isoformat(), admin_reply, request_id))
            else:
                cursor.execute("UPDATE admin_requests SET status = ? WHERE id = ?", (status, request_id))
            conn.commit()

    # ==================== BROADCAST ====================

    def log_broadcast(self, admin_id: int, message: str, recipient_count: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO broadcast_log (admin_id, message, recipient_count) VALUES (?, ?, ?)",
                           (admin_id, message, recipient_count))
            conn.commit()

    # ==================== LUG'AT ====================

    def get_lugat_books(self, level: str):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM lugat_books WHERE level = ? ORDER BY id", (level,))
            return [dict(row) for row in cursor.fetchall()]

    def get_lugat_book_by_id(self, book_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM lugat_books WHERE id = ?", (book_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_lugat_chapters(self, book_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM lugat_chapters WHERE book_id = ? ORDER BY order_num", (book_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_lugat_chapter_by_id(self, chapter_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM lugat_chapters WHERE id = ?", (chapter_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_lugat_words(self, chapter_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM lugat_words WHERE chapter_id = ? ORDER BY order_num", (chapter_id,))
            return [dict(row) for row in cursor.fetchall()]

    # ==================== SAYFA ====================

    def get_sayfa_materials(self, book_key: str):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sayfa_materials WHERE book_key = ? ORDER BY order_num", (book_key,))
            return [dict(row) for row in cursor.fetchall()]

    def get_sayfa_material_by_id(self, mat_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sayfa_materials WHERE id = ?", (mat_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # ==================== KITOB ====================

    def get_kitob_books(self, level: str):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM kitob_books WHERE level = ? ORDER BY id", (level,))
            return [dict(row) for row in cursor.fetchall()]

    def get_kitob_book_by_id(self, book_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM kitob_books WHERE id = ?", (book_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_kitob_materials(self, book_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM kitob_materials WHERE book_id = ? ORDER BY order_num", (book_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_kitob_material_by_id(self, mat_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM kitob_materials WHERE id = ?", (mat_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # ==================== AKTIV SPRECHEN ====================

    def get_aktiv_topics(self, level: str):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM aktiv_topics WHERE level = ? ORDER BY topic_id", (level,))
            return [dict(row) for row in cursor.fetchall()]

    def get_aktiv_topic_by_id(self, topic_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM aktiv_topics WHERE id = ?", (topic_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_aktiv_vocab(self, topic_id: int, limit: int = 25):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM aktiv_vocab WHERE topic_id = ? LIMIT ?", (topic_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_aktiv_story(self, topic_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM aktiv_stories WHERE topic_id = ?", (topic_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_aktiv_grammar(self, topic_id: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM aktiv_grammar WHERE topic_id = ?", (topic_id,))
            return [dict(row) for row in cursor.fetchall()]

    # ==================== TEST ====================

    def save_test_result(self, user_id: int, level: str, score: int, total_questions: int, correct: int, time_taken: int):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO test_results (user_id, level, score, total_questions, correct_answers, time_taken)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, level, score, total_questions, correct, time_taken))
            conn.commit()

    def get_test_results(self, user_id: int, limit: int = 10):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM test_results WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]


# Singleton
_db_instance = None

def get_db() -> Database:
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
