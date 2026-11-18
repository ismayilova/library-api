# Refactoring Report: Campus Library API

Line numbers in the diagnosis refer to the **original** `app.py` (555 lines, commit `1b6f3b3`).

## 1. Diagnose

| # | Problem | Where (original `app.py`) | Mainly | Future change it makes harder |
|---|---|---|---|---|
| 1 | **One file does everything**: HTTP, SQL, library rules, email, validation, JSON shaping and database setup. | The whole file | Cohesion (coincidental) | Any change means reading 555 lines. Two people can't work on different areas without conflicts. |
| 2 | **Every route opens the database itself** with `sqlite3.connect("library.db")` and writes SQL. There are 17 connections and 16 routes containing SQL. Every error path must remember `conn.close()`. | Lines 105-538 | Coupling (external) | Moving to another database, changing the file path, or adding connection settings means editing 17 places. One missed `close()` leaks a connection. |
| 3 | **Rows are read by position**: `r[4]`, `loan[6]`, `member[3]`. A row is passed around and only part of it is used. | e.g. 113, 152, 223-229, 325, 344 | Coupling (stamp) | Adding or reordering a column silently breaks the code. Nobody can tell what `loan[6]` means without checking the schema. |
| 4 | **The fine rate `0.50` is repeated 7 times**, sometimes written `0.5`. | 227, 260, 290, 337, 394, 528, 548 | Cohesion (one rule scattered) | Changing the rate, adding a grace period or a maximum fine means finding every copy. Missing one gives wrong amounts in one report. |
| 5 | **"How much does the member owe / how many loans are open" is copy-pasted** in `member_loans`, `create_loan` and `report_summary`. The loan limits `3`/`5` and the `14`-day period are also duplicated. | 219-244, 329-348, 542-550, 350, 442 | Cohesion | A new rule (for example, a third member type) has to be changed in several places, and the copies can drift apart. |
| 6 | **`CURRENT_MEMBER` is a global** that `create_loan` and `renew_loan` set so `notify()` can read it. `return_book` and `pay_fine` skip `notify` and write the outbox directly. | 10, 97, 361, 445, 403, 487 | Coupling (common) | `notify()` can't be understood or tested alone. Two requests at once can send one member's email to another. Email sending is done two different ways. |
| 7 | **A word passed in chooses the behavior**: `check(value, "isbn")` and `notify("checkout", ..., send=True)`. An unknown `kind` silently returns `False` or sends a generic notice. | 63-77, 84-97 | Coupling (control) and cohesion | Adding a new kind means editing the middle of a growing `if/elif`. A typo in the string is only found at run time. |
| 8 | **Email is hard-wired**: `outbox.txt` is opened in 3 places and message text is built by string concatenation inside the routes. | 96, 403, 487 | Coupling (external) | Switching to a real mail server or changing the wording means editing business logic. |
| 9 | **Rules and HTTP are mixed**: rules `return jsonify(...), 409` directly, so they can't run without Flask and a database. | Every route | Coupling | The fine rule or loan limit can't be unit-tested, or reused from a script or another interface. |
| 10 | **The same JSON dictionary is built again and again**: the loan dict 6 times, the book dict 3 times, the member dict 3 times. | 263, 291, 364, 409, 452, 492 (loans) | Cohesion (duplication) | Adding a field to a loan means 6 edits, and missing one changes only some responses. |
| 11 | **Importing the file has side effects**: `init_db()` (which `DROP`s all tables) lives next to the routes, and the file calls it at import time. | 13-57, 554-555 | Cohesion | Setup, schema and seed data can't be changed or reused separately from the web code. |

## 2. Refactor

The code now has the layers from `refactoring-steps.md`, and each layer only calls the one below it:

```text
Router       reads the request, returns JSON          routers/book_router.py, member_router.py, loan_router.py, report_router.py
  ↓
Service      applies the library's rules              book_service.py member_service.py loan_service.py  report_service.py
  ↓
Repository   runs the SQL                             book_repository.py member_repository.py loan_repository.py report_repository.py
  ↓
Database     db.py (connect, init_db)
```

The Service, Repository and Router layers each have one file per resource (`book_*`, `member_*`, `loan_*`) plus `report_*` for the report endpoints. Shared helpers, each with one job: `errors.py` (`api_error(message, status_code)`, the 400/404/409 shortcuts and the Flask error handler), `utils/validation.py` (is the input valid?), `utils/checks.py` (yes/no questions such as `is_overdue` or `has_reached_loan_limit`), `utils/fines.py` (the fine rule and `money`), and `notifications.py`. Notifications are mocked: `MockEmailSender` records every message in memory and appends it to `outbox.txt`, and `set_sender()` swaps in a real sender later. `app.py` only creates the Flask app, registers the four blueprints, installs the error handler and creates the database on first start.

What went where:

- **Rules** are in services. Constants such as `LOAN_DAYS`, `RENEWAL_DAYS`, `MAX_RENEWALS` and `LOAN_LIMITS` are at the top of `loan_service.py`. Services raise `LibraryError` instead of building HTTP responses.
- **`CURRENT_MEMBER`, `check()`, `notify()` and `money()` are gone** from `app.py`. Services pass the member's email straight to `send_email`.
- **Rows are read by column name** (`loan["due_date"]`) using `sqlite3.Row`.
- **Email wording, error messages, status codes, URLs and JSON are unchanged.**

### Checks

- `python -m unittest`: **63 tests, OK** (the original 53, unchanged, plus 10 new ones in `test_units.py` for fines, checks, validation, the error helper and the mock notifier).
- I also ran the original `app.py` and the new code through the same 74 requests (all the endpoints plus edge cases like missing request bodies, invalid fields, unknown routes, wrong methods, overdue renewals and the fine flow). Every status code, JSON body and `outbox.txt` line was **identical**.

## Measure your work

| Measure | Before | After |
|---|---|---|
| Tests passing | 53 / 53 | 53 / 53 |
| Files with code (not counting tests) | 1 | 19 |
| Lines in the largest file | 555 (`app.py`) | 104 (`services/loan_service.py`); `app.py` is 17 |
| Places that open the database | 17 | 1 (`db.py`) |
| Places where the fine rate appears | 7 | 1 (`utils/fines.py`) |
| Route handlers containing SQL | 16 | 0 |
| Places edited for the change request | n/a | *Not done: no requirement was provided (see below)* |
| Can the fine rule be tested without HTTP or a database? | No | Yes: `fines.fine_for("2026-01-01")` and `loan_service.amount_owed(loan)` take plain values |

For a feel of the new structure (these are examples, **not** your instructor's change request), changing the fine rate means editing 1 place (`FINE_PER_DAY` in `utils/fines.py`), changing the loan period 1 place (`LOAN_DAYS`), and changing the email wording 1 place (the call in `loan_service.py`).

## Questions to answer

**1. Which module is the most cohesive? Describe its one job in a sentence.**

`utils/fines.py`: it knows how late a loan is and what that lateness costs, and it formats money. Everything in it is about the fine rule, and nothing in it knows about HTTP, SQL or email. (`notifications.py` and `utils/validation.py` are similarly focused.)

**2. Which dependency did you remove, and what can now change independently because of that?**

The biggest one is the routes' dependency on SQL and on the database file. Now only `db.py` knows how to open the database, and only the repositories know the table layout. The database, the schema or the file path can change without touching a rule or a route.

Two others: the rules no longer depend on Flask, so they can be tested and reused without HTTP, and `notify()` no longer depends on the hidden global `CURRENT_MEMBER`, so email sending can change (real mail server, new wording) without touching the loan logic.

**3. What coupling remains, and why did you accept it?**

- **Services and routes still receive whole database rows** (stamp coupling) and read columns by name. Renaming a column would still ripple into `loan_service.py` and the route JSON functions. Reading by name is already much safer than by position, and adding a separate loan class would add code without helping this small app.
- **`loan_service` depends on other domains' repositories and on `notifications`.** A checkout really does need the book, the member and an email, so I kept these as one-way, visible imports. There are no circular imports, and no new file imports `app`.
- **`loan_repository.create_loan` also updates the `books` table**, so a loan and the book's availability are saved in one transaction. Keeping them together is better than risking a loan with the book still marked available.
- **`fines.days_late` reads today's date directly**, so tests of date-dependent rules need to build dates relative to today (as `test_api.py` does) rather than fix the clock.
- **`library.db` and `outbox.txt` stay as relative paths** (required by the rules). The coupling to those files now sits in one constant each (`DB_PATH`, `OUTBOX_PATH`).
- **Routes import `fines` for `money()`**, so they know about a helper outside the service layer. It is only number formatting, so I accepted it.

## Change request

Your instructor gives you this requirement in class, and none was included in the files, so this step has **not been done**. Once you have it, implement it in the refactored code and record the number of places you edited in the table above.
