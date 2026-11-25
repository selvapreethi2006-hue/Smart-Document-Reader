"""SQLite database for saving documents, summaries, and chat history."""

import sqlite3
import json
from datetime import datetime
import os

DB_PATH = "smart_doc_history.db"

def init_db():
    """Create tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Documents table
    c.execute('''CREATE TABLE IF NOT EXISTS documents
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  filename TEXT,
                  text TEXT,
                  summary TEXT,
                  info TEXT,
                  stats TEXT,
                  saved_at TEXT)''')
    # Chat history table
    c.execute('''CREATE TABLE IF NOT EXISTS chat_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  doc_id INTEGER,
                  question TEXT,
                  answer TEXT,
                  saved_at TEXT,
                  FOREIGN KEY(doc_id) REFERENCES documents(id))''')
    conn.commit()
    conn.close()

def save_document(filename, text, summary, info, stats):
    """Save a new document and return its ID."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''INSERT INTO documents (filename, text, summary, info, stats, saved_at)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (filename, text, summary, json.dumps(info), json.dumps(stats), now))
    doc_id = c.lastrowid
    conn.commit()
    conn.close()
    return doc_id

def save_chat(doc_id, question, answer):
    """Save a Q&A pair linked to a document."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''INSERT INTO chat_history (doc_id, question, answer, saved_at)
                 VALUES (?, ?, ?, ?)''', (doc_id, question, answer, now))
    conn.commit()
    conn.close()

def get_all_documents():
    """Retrieve all saved documents (without full text to keep it fast)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''SELECT id, filename, summary, saved_at FROM documents ORDER BY id DESC''')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_document(doc_id):
    """Retrieve a single document with all data."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
    row = c.fetchone()
    conn.close()
    if row:
        d = dict(row)
        d['info'] = json.loads(d['info']) if d['info'] else {}
        d['stats'] = json.loads(d['stats']) if d['stats'] else {}
        return d
    return None

def get_chats_for_doc(doc_id):
    """Retrieve chat history for a specific document."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT question, answer, saved_at FROM chat_history WHERE doc_id = ? ORDER BY id ASC', (doc_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def search_documents(query):
    """Search documents by filename or text content."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''SELECT id, filename, summary, saved_at FROM documents 
                 WHERE filename LIKE ? OR text LIKE ? ORDER BY id DESC''',
              (f"%{query}%", f"%{query}%"))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_document(doc_id):
    """Delete a document and its chat history."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM chat_history WHERE doc_id = ?', (doc_id,))
    c.execute('DELETE FROM documents WHERE id = ?', (doc_id,))
    conn.commit()
    conn.close()

# Initialize on import
init_db()