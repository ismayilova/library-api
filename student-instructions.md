# Student Instructions

You don't need any Python experience for this activity. You will read working code, then split it up one small step at a time.

**Your goal:** make the code easier to change, without changing what the API does.

- **Coupling** is how much one piece of code depends on another. You want **less**.
- **Cohesion** is how well the code in one place belongs together. You want **more**.

## Before you start

1. Open the `library-api` folder in VS Code, using **File > Open Folder**.
2. Open the terminal with **Terminal > New Terminal**.
3. Activate your environment. You should see `(.venv)` at the start of the line.

   ```bash
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   ```

4. Run the tests:

   ```bash
   python -m unittest
   ```

You're ready if the output says `Ran 53 tests` and ends with `OK`. If it doesn't, ask your instructor now.

## The Python you need

This is enough to read `app.py`. You don't need to memorize it, so come back to it whenever you need to.

### Variables and text

```python
title = "Clean Code"
message = "You checked out " + title
```

`=` stores a value in a name, and `+` joins pieces of text.

### Indentation

Python uses spaces to show which lines belong together:

```python
if title == "Clean Code":
    print("Found it")
else:
    print("Not this one")
```

`==` asks "are these equal?". The lines indented under `if` run only when the answer is yes. **Wrong indentation is the most common beginner error**, so keep lines lined up exactly.

### Functions

A function is a named piece of code. It takes inputs and can return a result:

```python
def add_tax(price):
    return price * 1.2


total = add_tax(100)
```

### Lists and loops

A list holds several values, and `for` runs code once for each one:

```python
names = ["Sam", "Noor", "Alex"]
for name in names:
    print(name)
```

### Tuples, where counting starts at 0

A database row in `app.py` is a tuple, which is a fixed list of values. You read a value by its position, **starting at 0**:

```python
book = (1, "Clean Code", "Robert C. Martin")
print(book[1])
```

This prints `Clean Code`, the second value.

### Dictionaries

A dictionary stores values by name instead of by position:

```python
book = {"id": 1, "title": "Clean Code"}
print(book["title"])
```

### Using code from another file

If you have a file called `fines.py`, another file can use it like this:

```python
import fines

amount = fines.fine_for("2026-01-15")
```

Don't write `.py` in the `import` line.

### Three things you'll see in `app.py`

| Code | What it means |
|---|---|
| `@app.route("/books", methods=["GET"])` | Run the function below when someone requests `GET /books`. |
| `return jsonify({"error": "book not found"}), 404` | Send this JSON back, with status code 404. |
| `conn.execute("SELECT * FROM books")` | Run this SQL on the database. |

## What happens in `app.py`

Almost every function follows the same path. It helps to look out for these steps when you read:

```text
Request arrives → check the input → run SQL → apply library rules → send email → return JSON
```

The database has three tables:

| Table | Columns, in order |
|---|---|
| `books` | `id`, `title`, `author`, `isbn`, `available` |
| `members` | `id`, `name`, `email`, `type` |
| `loans` | `id`, `book_id`, `member_id`, `due_date`, `returned`, `fine`, `fine_paid`, `renewals`, `checked_out` |

To try the API yourself, see the [API documentation](API.md). It shows how to call each request and what comes back.

## Step 1: Refactor the code (40 minutes)

Follow the [refactoring steps](refactoring-steps.md). They take you from looking at the API, through naming the main issue, to splitting the code by domain.

Follow the same routine for every step:

1. **Make one small change.** Use **Cmd+F** (Windows: **Ctrl+F**) to find the code, and save with **Cmd+S** (Windows: **Ctrl+S**).
2. **Run the tests:** `python -m unittest`
3. **If you see `OK`,** save your progress:

   ```bash
   git add .
   git commit -m "Describe what you just did"
   ```

4. **If the tests fail,** check the table below. To go back to your last commit, run `git restore app.py`.

To create a new file, right-click an empty area of the file list in VS Code and choose **New File**. New files go **next to `app.py`**, not in a subfolder.

## Reading an error

Python prints the most useful line **last**, so read from the bottom up. The lines above it name the file and line number.

| Error | What it means | Fix |
|---|---|---|
| `IndentationError` | The spaces at the start of a line are wrong. | Line it up with the lines around it. |
| `SyntaxError` | Python can't read the line, often because of a missing `)`, `"` or `:`. | Check the line it names, and the line just above it. |
| `NameError: name 'fines' is not defined` | You used a name that doesn't exist in this file. | Add the missing `import`, or check the spelling. |
| `ModuleNotFoundError: No module named 'fines'` | Python can't find that file. | Check that the file is next to `app.py`, is saved and has the right name. |
| `ModuleNotFoundError: No module named 'flask'` | Your environment isn't active. | Activate it, so that you see `(.venv)`. |
| `AttributeError: module 'fines' has no attribute 'fine_for'` | The file exists, but that function isn't in it. | Check the spelling, and save the file. |
| `ImportError: ... circular import` | Two files import each other. | New files must never import `app`. |
| `FAIL: test_...` | The code runs, but the API's behavior changed. | Compare your change with the step again. |

If you can't fix it in a few minutes, run `git restore app.py` and try again, or ask for help. That only undoes changes to `app.py` since your last commit, which is why you commit after each step.

## Step 2: Change request (10 minutes)

Your instructor will give you a new requirement. Add it to your improved code, and **count the places you had to edit**.

## Rules

1. Don't change `test_api.py`.
2. Keep `app.py` in this folder, and make sure it still provides `app` and `init_db`.
3. Keep `library.db` and `outbox.txt` as plain relative file names.
4. Keep the same URLs, status codes and JSON.
