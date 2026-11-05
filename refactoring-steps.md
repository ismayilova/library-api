# Refactoring Steps

You will take one big file and split it up, one small step at a time.

## The three rules

1. **Change one small thing.**
2. **Run the tests:** `python -m unittest`
3. **If you see `OK`, commit and continue.** If you don't, fix it or undo with `git restore app.py`.

```bash
git add .
git commit -m "Describe what you just did"
```

## Where we're going

Each layer has one job and only talks to the layer below it:

```text
Route        reads the request, returns JSON
  ↓
Service      applies the library's rules
  ↓
Repository   runs the SQL
  ↓
Database
```

## Step 1: Look at the API

Before changing code, learn what it does. Start the API and open these in your browser:

- <http://localhost:8000/books>
- <http://localhost:8000/members>
- <http://localhost:8000/loans>
- <http://localhost:8000/reports/summary>

Then look through the [API documentation](API.md). **What the API does must stay exactly the same.** The tests check that for you.

Stop the API with `Ctrl+C` when you're done.

## Step 2: Name the main issue

Open `app.py` and skim it. The main issue is simple: **everything is in one place.**

That file does HTTP, SQL, library rules, email, validation and database setup. These jobs have little to do with each other, which is **coincidental cohesion**, the weakest kind.

Because it's all together, the parts also depend on each other in ways that are hard to see. Find one example of each type of coupling:

| Coupling type | What it means | Find it in `app.py` |
|---|---|---|
| Common | Functions share global data | `CURRENT_MEMBER` |
| External | Code depends on an outside tool or file | `sqlite3.connect("library.db")`, `outbox.txt` |
| Control | A word passed in chooses what the function does | `check(value, kind)`, `notify(kind, ...)` |
| Stamp | A function gets a whole row but uses only part of it | `CURRENT_MEMBER[2]` |

## Step 3: Decide the domains

A **domain** is one area of the problem. Look at the URLs in the API, and decide which domains you see before reading on.

The answer:

| Domain | URLs |
|---|---|
| Books | `/books` |
| Members | `/members` |
| Loans | `/loans` |
| Reports | `/reports` |

Each domain will get its own three files:

| Domain | Repository | Service | Routes |
|---|---|---|---|
| Books | `book_repository.py` | `book_service.py` | `book_routes.py` |
| Members | `member_repository.py` | `member_service.py` | `member_routes.py` |
| Loans | `loan_repository.py` | `loan_service.py` | `loan_routes.py` |
| Reports | `report_repository.py` | `report_service.py` | `report_routes.py` |

New files go **next to `app.py`**.

## Step 4: Move the database code

**Goal:** Only one file knows how to open the database.

1. Create `db.py`:

   ```python
   import sqlite3
   from datetime import date, timedelta

   DB_PATH = "library.db"


   def connect():
       conn = sqlite3.connect(DB_PATH)
       conn.row_factory = sqlite3.Row
       return conn
   ```

   The `row_factory` line lets you read columns by name, such as `loan["due_date"]`.

2. Cut the whole `init_db` function out of `app.py` and paste it at the bottom of `db.py`. In the pasted function, change the first `conn` line to `conn = connect()`.

3. At the top of `app.py`, add:

   ```python
   import db
   from db import init_db
   ```

4. In `app.py`, replace every `sqlite3.connect("library.db")` with `db.connect()`, using **Cmd+Option+F** (Windows: **Ctrl+H**). Then delete the `import sqlite3` line.

**Run the tests, then commit.**

## Step 5: Move the SQL into repositories

**Goal:** Routes contain no SQL. A repository function runs a query and returns the result.

### 5a. Books (full example)

1. Create `book_repository.py`:

   ```python
   import db


   def list_books(only_available):
       conn = db.connect()
       if only_available:
           rows = conn.execute("SELECT * FROM books WHERE available = 1").fetchall()
       else:
           rows = conn.execute("SELECT * FROM books").fetchall()
       conn.close()
       return rows


   def get_book(book_id):
       conn = db.connect()
       book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
       conn.close()
       return book


   def create_book(title, author, isbn):
       conn = db.connect()
       cur = conn.execute(
           "INSERT INTO books (title, author, isbn, available) VALUES (?, ?, ?, 1)",
           (title, author, isbn),
       )
       conn.commit()
       book = conn.execute("SELECT * FROM books WHERE id = ?", (cur.lastrowid,)).fetchone()
       conn.close()
       return book


   def delete_book(book_id):
       conn = db.connect()
       conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
       conn.commit()
       conn.close()


   def count_books():
       conn = db.connect()
       total = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
       conn.close()
       return total
   ```

2. At the top of `app.py`, add `import book_repository`.

3. Replace the whole books section of `app.py` with this:

   ```python
   def book_json(book):
       return {"id": book["id"], "title": book["title"], "author": book["author"], "isbn": book["isbn"], "available": bool(book["available"])}


   @app.route("/books", methods=["GET"])
   def list_books():
       rows = book_repository.list_books(request.args.get("available") == "true")
       result = []
       for r in rows:
           result.append(book_json(r))
       return jsonify(result)


   @app.route("/books/<int:book_id>", methods=["GET"])
   def get_book(book_id):
       r = book_repository.get_book(book_id)
       if r is None:
           return jsonify({"error": "book not found"}), 404
       return jsonify(book_json(r))


   @app.route("/books", methods=["POST"])
   def create_book():
       data = request.get_json(silent=True) or {}
       if not data.get("title") or not data.get("author"):
           return jsonify({"error": "title and author are required"}), 400
       if not check(data.get("isbn"), "isbn"):
           return jsonify({"error": "invalid isbn"}), 400
       r = book_repository.create_book(data["title"], data["author"], data["isbn"])
       return jsonify(book_json(r)), 201


   @app.route("/books/<int:book_id>", methods=["DELETE"])
   def delete_book(book_id):
       r = book_repository.get_book(book_id)
       if r is None:
           return jsonify({"error": "book not found"}), 404
       if r["available"] == 0:
           return jsonify({"error": "book is on loan"}), 409
       book_repository.delete_book(book_id)
       return "", 204
   ```

**Run the tests, then commit.**

### 5b-5d. Members, loans and reports

Now do the same for the other domains, in this order. Copy each query out of its route, and use column names when you move code.

| Step | File to create | Functions to write |
|---|---|---|
| 5b | `member_repository.py` | `list_members()`, `get_member(member_id)`, `get_member_by_email(email)`, `create_member(name, email, member_type)` |
| 5b | `loan_repository.py` | `list_loans()`, `list_loans_for_member(member_id)`, `get_loan(loan_id)`, `create_loan(book_id, member_id, due_date, checked_out)`, `mark_returned(loan_id, book_id, fine)`, `extend_loan(loan_id, new_due_date)`, `mark_fine_paid(loan_id)` |
| 5d | `report_repository.py` | `list_open_loans_with_details()`, using the query in `report_overdue` |

Then update the routes, and **run the tests and commit after each line of this list**:

- **5b:** Member routes. `member_loans` uses `loan_repository.list_loans_for_member`.
- **5c:** Loan routes. These also call `book_repository` and `member_repository`.
- **5d:** Report routes. `report_summary` uses `book_repository.count_books` and `loan_repository.list_loans`.

Column names, in order:

| Table | Columns |
|---|---|
| `books` | `id`, `title`, `author`, `isbn`, `available` |
| `members` | `id`, `name`, `email`, `type` |
| `loans` | `id`, `book_id`, `member_id`, `due_date`, `returned`, `fine`, `fine_paid`, `renewals`, `checked_out` |

**Check when you're done:** searching `app.py` for `execute` should find nothing.

## Step 6: Move the rules into services

**Goal:** Every route calls a service function. Routes contain no rules.

### 6a. Create the shared files

These small files hold things that several services need. Create all four:

**`errors.py`** lets a service report a problem without knowing about HTTP responses:

```python
class LibraryError(Exception):
    def __init__(self, message, status):
        self.message = message
        self.status = status


def bad_request(message):
    return LibraryError(message, 400)


def not_found(message):
    return LibraryError(message, 404)


def conflict(message):
    return LibraryError(message, 409)
```

**`validation.py`**:

```python
import re
from datetime import date


def is_valid_email(value):
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(value)) is not None


def is_valid_isbn(value):
    digits = str(value).replace("-", "")
    return digits.isdigit() and len(digits) in (10, 13)


def is_valid_date(value):
    try:
        date.fromisoformat(str(value))
        return True
    except ValueError:
        return False


def is_valid_member_type(value):
    return value in ("student", "staff")
```

**`fines.py`**:

```python
from datetime import date

FINE_PER_DAY = 0.50


def days_late(due_date):
    return (date.today() - date.fromisoformat(due_date)).days


def fine_for(due_date):
    return max(0, days_late(due_date)) * FINE_PER_DAY


def money(amount):
    return round(float(amount), 2)
```

**`notifications.py`**:

```python
OUTBOX_PATH = "outbox.txt"


def send_email(email, subject, body):
    with open(OUTBOX_PATH, "a") as f:
        f.write("TO: " + email + " | SUBJECT: " + subject + " | BODY: " + body + "\n")
```

Then, in `app.py`, add these two imports at the top:

```python
import fines
from errors import LibraryError
```

And add this just below `app = Flask(__name__)`:

```python
@app.errorhandler(LibraryError)
def handle_library_error(error):
    return jsonify({"error": error.message}), error.status
```

**Run the tests, then commit.**

### 6b. Books (full example)

1. Create `book_service.py`:

   ```python
   import book_repository
   import validation
   from errors import bad_request, conflict, not_found


   def list_books(only_available):
       return book_repository.list_books(only_available)


   def get_book(book_id):
       book = book_repository.get_book(book_id)
       if book is None:
           raise not_found("book not found")
       return book


   def create_book(data):
       if not data.get("title") or not data.get("author"):
           raise bad_request("title and author are required")
       if not validation.is_valid_isbn(data.get("isbn")):
           raise bad_request("invalid isbn")
       return book_repository.create_book(data["title"], data["author"], data["isbn"])


   def delete_book(book_id):
       book = get_book(book_id)
       if book["available"] == 0:
           raise conflict("book is on loan")
       book_repository.delete_book(book_id)
   ```

2. At the top of `app.py`, add `import book_service`.

3. Replace the four book routes in `app.py`. Keep `book_json`. The routes are now very short:

   ```python
   @app.route("/books", methods=["GET"])
   def list_books():
       only_available = request.args.get("available") == "true"
       result = []
       for book in book_service.list_books(only_available):
           result.append(book_json(book))
       return jsonify(result)


   @app.route("/books/<int:book_id>", methods=["GET"])
   def get_book(book_id):
       return jsonify(book_json(book_service.get_book(book_id)))


   @app.route("/books", methods=["POST"])
   def create_book():
       data = request.get_json(silent=True) or {}
       return jsonify(book_json(book_service.create_book(data))), 201


   @app.route("/books/<int:book_id>", methods=["DELETE"])
   def delete_book(book_id):
       book_service.delete_book(book_id)
       return "", 204
   ```

**Run the tests, then commit.**

### 6c-6e. Loans, members and reports

Do these in this order, because members and reports use the loan rules. For each route, move its logic into a service function and change it like this:

| In the route | In the service |
|---|---|
| `return jsonify({"error": "..."}), 400` | `raise bad_request("...")` |
| `return jsonify({"error": "..."}), 404` | `raise not_found("...")` |
| `return jsonify({"error": "..."}), 409` | `raise conflict("...")` |
| `check(value, "email")` | `validation.is_valid_email(value)` |
| `max(0, days_late) * 0.50` | `fines.fine_for(loan["due_date"])` |
| Writing to `outbox.txt`, or `notify(...)` | `notifications.send_email(email, subject, body)` |
| `14`, or the limits `3` and `5` | Constants at the top of `loan_service.py` |

| Step | File to create | Functions to write |
|---|---|---|
| 6c | `loan_service.py` | `amount_owed(loan)`, `total_owed(loans)`, `count_open_loans(loans)`, `current_fine(loan)`, `is_overdue(loan)`, `list_loans(only_overdue)`, `get_loan(loan_id)`, `create_loan(data)`, `return_book(loan_id)`, `renew_loan(loan_id)`, `pay_fine(loan_id)` |
| 6d | `member_service.py` | `list_members()`, `get_member(member_id)`, `create_member(data)`, `member_account(member_id)` |
| 6e | `report_service.py` | `overdue_report()`, `summary_report()` |

**Run the tests and commit after each one.** Keep the wording of each email and error exactly as it is, because the tests check it.

**Clean up when you're done.** Delete these from `app.py`, then run the tests and commit:

- `check`, `notify` and `money`
- `CURRENT_MEMBER`
- any imports that are no longer used

## Step 7: Move the routes

**Goal:** `app.py` only connects everything together.

1. Create `book_routes.py`, and move `book_json` and the book routes into it. Change `@app.route` to `@bp.route`:

   ```python
   from flask import Blueprint, jsonify, request

   import book_service

   bp = Blueprint("books", __name__)
   ```

2. Do the same for `member_routes.py`, `loan_routes.py` and `report_routes.py`, with their own imports. **Run the tests and commit after each one.**

3. When all four are done, `app.py` should be this short:

   ```python
   import os

   from flask import Flask, jsonify

   import book_routes
   import loan_routes
   import member_routes
   import report_routes
   from db import init_db
   from errors import LibraryError

   app = Flask(__name__)
   app.register_blueprint(book_routes.bp)
   app.register_blueprint(member_routes.bp)
   app.register_blueprint(loan_routes.bp)
   app.register_blueprint(report_routes.bp)


   @app.errorhandler(LibraryError)
   def handle_library_error(error):
       return jsonify({"error": error.message}), error.status


   if not os.path.exists("library.db"):
       init_db()
   ```

Each time you move a group of routes, add its `import` and `register_blueprint` lines to `app.py`.

**Run the tests, then commit.**

## How far should you get?

You won't necessarily finish, and that's fine. Getting the **books domain through Steps 4-6** is a good result, because the other domains repeat the same pattern. Loans is the largest, so expect it to take the longest.

## See what you changed

Compare the starting file with your result:

| Question | Before | After |
|---|---|---|
| Files with code | 1 | Up to 18 |
| Lines in the largest file | 555 | About 130 |
| Places that open the database | 17 | 1 |
| Places where the fine rate appears | 7 | 1 |
| Routes containing SQL | 16 | 0 |
