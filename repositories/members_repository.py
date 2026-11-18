from db import get_connection


def find_all():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM members").fetchall()
    conn.close()
    return rows


def find_by_id(member_id):
    conn = get_connection()
    r = conn.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
    conn.close()
    return r


def find_by_email(email):
    conn = get_connection()
    r = conn.execute("SELECT * FROM members WHERE email = ?", (email,)).fetchone()
    conn.close()
    return r


def create(name, email, member_type):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO members (name, email, type) VALUES (?, ?, ?)",
        (name, email, member_type),
    )
    conn.commit()
    r = conn.execute("SELECT * FROM members WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.close()
    return r


def delete(member_id):
    conn = get_connection()
    conn.execute("DELETE FROM members WHERE id = ?", (member_id,))
    conn.commit()
    conn.close()