import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "bot_users.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            lang TEXT DEFAULT 'uz',
            fav_team_id INTEGER DEFAULT NULL,
            fav_team_name TEXT DEFAULT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notified_goals (
            match_id INTEGER,
            goal_id TEXT,
            PRIMARY KEY (match_id, goal_id)
        )
    """)
    conn.commit()
    conn.close()

def add_user(telegram_id, lang="uz"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO users (telegram_id, lang) VALUES (?, ?)", (telegram_id, lang))
        # If exists, maybe update lang?
        # cursor.execute("UPDATE users SET lang = ? WHERE telegram_id = ?", (lang, telegram_id))
        conn.commit()
    except Exception as e:
        print(f"DB Error (add_user): {e}")
    finally:
        conn.close()

def set_lang(telegram_id, lang):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET lang = ? WHERE telegram_id = ?", (lang, telegram_id))
    if cursor.rowcount == 0:
        add_user(telegram_id, lang)
    conn.commit()
    conn.close()

def get_user(telegram_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "lang": row[1], "fav_team_id": row[2], "fav_team_name": row[3]}
    return None

def set_favorite(telegram_id, team_id, team_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Check if currently favorite. If same, remove it (Toggle). 
    # Or strict set? Let's implement set/unset logic in handler, here just set.
    # But wait, user asked to select favorite. Usually one favorite? Or text implies generic "favorite team". 
    # Let's assume single favorite for simplicity in V1.
    
    cursor.execute("UPDATE users SET fav_team_id = ?, fav_team_name = ? WHERE telegram_id = ?", (team_id, team_name, telegram_id))
    conn.commit()
    conn.close()

def remove_favorite(telegram_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET fav_team_id = NULL, fav_team_name = NULL WHERE telegram_id = ?", (telegram_id,))
    conn.commit()
    conn.close()

def get_users_by_team(team_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id, lang FROM users WHERE fav_team_id = ?", (team_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "lang": r[1]} for r in rows]

def get_all_favorite_teams():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT fav_team_id FROM users WHERE fav_team_id IS NOT NULL")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

def is_goal_notified(match_id, goal_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM notified_goals WHERE match_id = ? AND goal_id = ?", (match_id, goal_id))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def mark_goal_notified(match_id, goal_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO notified_goals (match_id, goal_id) VALUES (?, ?)", (match_id, goal_id))
    conn.commit()
    conn.close()
def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id, lang FROM users")
    rows = cursor.fetchall()
    conn.close()
    conn.close()
    return [{"id": r[0], "lang": r[1]} for r in rows]

def get_user_count():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_team_name(team_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT fav_team_name FROM users WHERE fav_team_id = ? LIMIT 1", (team_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "Team"
