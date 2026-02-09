import psycopg2
from psycopg2.extras import RealDictCursor
import os
import config

def get_connection():
    # Log connection attempt (hiding password for security)
    info = config.DATABASE_URL.split('@')[-1] if config.DATABASE_URL else "None"
    print(f"Connecting to database: {info}")
    return psycopg2.connect(config.DATABASE_URL, sslmode='require')

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id BIGINT PRIMARY KEY,
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
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (telegram_id, lang) 
            VALUES (%s, %s) 
            ON CONFLICT (telegram_id) DO NOTHING
        """, (telegram_id, lang))
        conn.commit()
    except Exception as e:
        print(f"DB Error (add_user): {e}")
    finally:
        conn.close()

def set_lang(telegram_id, lang):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET lang = %s WHERE telegram_id = %s", (lang, telegram_id))
    if cursor.rowcount == 0:
        cursor.execute("INSERT INTO users (telegram_id, lang) VALUES (%s, %s)", (telegram_id, lang))
    conn.commit()
    conn.close()

def get_user(telegram_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"id": row['telegram_id'], "lang": row['lang'], "fav_team_id": row['fav_team_id'], "fav_team_name": row['fav_team_name']}
    return None

def set_favorite(telegram_id, team_id, team_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET fav_team_id = %s, fav_team_name = %s WHERE telegram_id = %s", (team_id, team_name, telegram_id))
    conn.commit()
    conn.close()

def remove_favorite(telegram_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET fav_team_id = NULL, fav_team_name = NULL WHERE telegram_id = %s", (telegram_id,))
    conn.commit()
    conn.close()

def get_users_by_team(team_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT telegram_id, lang FROM users WHERE fav_team_id = %s", (team_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r['telegram_id'], "lang": r['lang']} for r in rows]

def get_all_favorite_teams():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT fav_team_id FROM users WHERE fav_team_id IS NOT NULL")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

def is_goal_notified(match_id, goal_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM notified_goals WHERE match_id = %s AND goal_id = %s", (match_id, goal_id))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def mark_goal_notified(match_id, goal_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notified_goals (match_id, goal_id) 
        VALUES (%s, %s) 
        ON CONFLICT (match_id, goal_id) DO NOTHING
    """, (match_id, goal_id))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT telegram_id, lang FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r['telegram_id'], "lang": r['lang']} for r in rows]

def get_user_count():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_team_name(team_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT fav_team_name FROM users WHERE fav_team_id = %s LIMIT 1", (team_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else "Team"
