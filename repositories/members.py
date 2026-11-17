from database import connect


def all_members():
    with connect() as db:
        return db.execute("SELECT * FROM members").fetchall()


def get(member_id):
    with connect() as db:
        return db.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()


def find_email(email):
    with connect() as db:
        return db.execute("SELECT * FROM members WHERE email = ?", (email,)).fetchone()


def add(name, email, member_type):
    with connect() as db:
        cur = db.execute("INSERT INTO members (name, email, type) VALUES (?, ?, ?)", (name, email, member_type))
        new_id = cur.lastrowid
    return get(new_id)
