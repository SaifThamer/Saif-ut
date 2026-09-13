# -*- coding: utf-8 -*-
"""
طبقة التعامل مع قاعدة البيانات (SQLite)
برنامج أرشفة الكتب الرسمية
"""

import sqlite3
import os
import shutil
from datetime import datetime

DB_NAME = "archive.db"


def get_db_path():
    """يرجع مسار قاعدة البيانات بجانب البرنامج"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, DB_NAME)


class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or get_db_path()
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS letters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                letter_number TEXT,
                sender_type TEXT,
                sender_name TEXT,
                letter_date TEXT,
                subject TEXT,
                notes TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.commit()
        conn.close()

    # ---------------- CRUD ----------------

    def add_letter(self, letter_number, sender_type, sender_name,
                   letter_date, subject, notes):
        conn = self._connect()
        cur = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("""
            INSERT INTO letters
            (letter_number, sender_type, sender_name, letter_date,
             subject, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (letter_number, sender_type, sender_name, letter_date,
              subject, notes, now, now))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return new_id

    def update_letter(self, letter_id, letter_number, sender_type,
                       sender_name, letter_date, subject, notes):
        conn = self._connect()
        cur = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("""
            UPDATE letters SET
                letter_number = ?, sender_type = ?, sender_name = ?,
                letter_date = ?, subject = ?, notes = ?, updated_at = ?
            WHERE id = ?
        """, (letter_number, sender_type, sender_name, letter_date,
              subject, notes, now, letter_id))
        conn.commit()
        conn.close()

    def delete_letter(self, letter_id):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM letters WHERE id = ?", (letter_id,))
        conn.commit()
        conn.close()

    def get_all(self, order_desc=True):
        conn = self._connect()
        cur = conn.cursor()
        order = "DESC" if order_desc else "ASC"
        cur.execute(f"SELECT * FROM letters ORDER BY id {order}")
        rows = cur.fetchall()
        conn.close()
        return rows

    def get_by_id(self, letter_id):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM letters WHERE id = ?", (letter_id,))
        row = cur.fetchone()
        conn.close()
        return row

    def search(self, keyword="", sender_type="", date_from="", date_to="",
               letter_number=""):
        """
        بحث شامل: keyword يبحث في (اسم الجهة، الموضوع، الملاحظات، رقم الكتاب)
        مع إمكانية تضييق البحث بنوع الجهة ونطاق التاريخ ورقم الكتاب
        """
        conn = self._connect()
        cur = conn.cursor()

        conditions = []
        params = []

        if keyword:
            conditions.append("""
                (sender_name LIKE ? OR subject LIKE ? OR notes LIKE ?
                 OR letter_number LIKE ? OR sender_type LIKE ?)
            """)
            like_kw = f"%{keyword}%"
            params.extend([like_kw, like_kw, like_kw, like_kw, like_kw])

        if sender_type:
            conditions.append("sender_type = ?")
            params.append(sender_type)

        if letter_number:
            conditions.append("letter_number LIKE ?")
            params.append(f"%{letter_number}%")

        if date_from:
            conditions.append("letter_date >= ?")
            params.append(date_from)

        if date_to:
            conditions.append("letter_date <= ?")
            params.append(date_to)

        query = "SELECT * FROM letters"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY id DESC"

        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        return rows

    def count(self):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM letters")
        c = cur.fetchone()["c"]
        conn.close()
        return c

    # ---------------- النسخ الاحتياطي والاستعادة ----------------

    def backup_to(self, target_path):
        """نسخ ملف قاعدة البيانات إلى مسار النسخة الاحتياطية"""
        shutil.copy2(self.db_path, target_path)

    def restore_from(self, source_path):
        """استعادة قاعدة البيانات من ملف نسخة احتياطية"""
        shutil.copy2(source_path, self.db_path)
