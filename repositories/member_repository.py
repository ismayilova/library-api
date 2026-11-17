from core import db
from models.member import Member


def list_members():
    conn = db.connect()
    rows = conn.execute("SELECT * FROM members").fetchall()
    conn.close()
    return [Member.from_row(row) for row in rows]


def get_member(member_id):
    conn = db.connect()
    member = conn.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
    conn.close()
    return Member.from_row(member)


def get_member_by_email(email):
    conn = db.connect()
    member = conn.execute("SELECT * FROM members WHERE email = ?", (email,)).fetchone()
    conn.close()
    return Member.from_row(member)


def create_member(name, email, member_type):
    conn = db.connect()
    cur = conn.execute("INSERT INTO members (name, email, type) VALUES (?, ?, ?)", (name, email, member_type))
    conn.commit()
    newId = cur.lastrowid
    member = conn.execute("SELECT * FROM members WHERE id = ?", (newId,)).fetchone()
    conn.close()
    return Member.from_row(member)


def delete_member(member_id):
    conn = db.connect()
    conn.execute("DELETE FROM loans WHERE member_id = ?", (member_id,))
    conn.execute("DELETE FROM members WHERE id = ?", (member_id,))
    conn.commit()
    conn.close()
