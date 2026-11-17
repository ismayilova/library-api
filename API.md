# API Documentation

This page shows how to call each request, what to send and what comes back.

## Before you call the API

Start the API in one terminal, and leave it running:

```bash
python -m flask run --port 8000
```

Every URL starts with `http://localhost:8000`. To stop the API, press `Ctrl+C`.

## How to send a request

Open a **second terminal** to send requests. For a `GET` request, you can also just paste the URL into your browser.

**macOS / Linux:**

```bash
curl -X POST http://localhost:8000/books -H "Content-Type: application/json" -d '{"title": "Dune", "author": "Frank Herbert", "isbn": "9780441013593"}'
```

**Windows (PowerShell):** use `Invoke-RestMethod` instead of `curl`, with the same URL and body:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/books -ContentType "application/json" -Body '{"title": "Dune", "author": "Frank Herbert", "isbn": "9780441013593"}'
```

Add `-i` after `curl` to see the status code as well as the response.

## About the examples

- The examples show a fresh database, and they run in the order shown on this page. To get a fresh database, stop the API, delete `library.db` and start the API again.
- If your data has changed, your IDs and values may differ.
- **Dates will differ.** The examples were recorded on 2026-11-05, and the sample loan's dates depend on the day the database was created.
- The fields in a response may appear in a different order. JSON doesn't depend on the order of fields.

## Status codes

| Code | Meaning | Example |
|---|---|---|
| 200 | Success | You got a book. |
| 201 | Created | You added a book. |
| 204 | Success, with nothing to return | You deleted a book. |
| 400 | Your request has missing or invalid data | The ISBN is invalid. |
| 404 | That item doesn't exist | There is no book 999. |
| 409 | The request breaks a library rule | The book is already on loan. |

Every error returns JSON with an `error` message:

```json
{"error": "book not found"}
```

If a request needs a body and you send one that isn't valid JSON, the API treats it as empty and returns 400.

## What the fields mean

| Field | Type | Meaning |
|---|---|---|
| `available` | true or false | Whether a book can be checked out |
| `type` | text | A member's type: `student` or `staff` |
| `due_date`, `checked_out` | text | A date in the form `YYYY-MM-DD` |
| `returned` | true or false | Whether the book has come back |
| `fine` | number | The fine charged when the book was returned. It stays `0.0` until then. |
| `current_fine` | number | What the loan's fine is right now, including a fine still building up |
| `fine_paid` | true or false | Whether the fine has been paid |
| `renewals` | number | How many times the loan has been renewed |

## Books

### List books

```text
GET /books
```

To list only books that can be checked out, use `GET /books?available=true`.

```bash
curl "http://localhost:8000/books?available=true"
```

**Response: 200**

```json
[
  {"id": 1, "title": "Clean Code", "author": "Robert C. Martin", "isbn": "9780132350884", "available": true},
  {"id": 2, "title": "The Pragmatic Programmer", "author": "Andrew Hunt", "isbn": "9780135957059", "available": true},
  {"id": 3, "title": "Design Patterns", "author": "Erich Gamma", "isbn": "9780201633610", "available": true},
  {"id": 4, "title": "Refactoring", "author": "Martin Fowler", "isbn": "9780134757599", "available": true}
]
```

### Get a book

```text
GET /books/<id>
```

```bash
curl http://localhost:8000/books/1
```

**Response: 200**

```json
{"id": 1, "title": "Clean Code", "author": "Robert C. Martin", "isbn": "9780132350884", "available": true}
```

| Error | Message | When |
|---|---|---|
| 404 | `book not found` | The book doesn't exist. |

### Add a book

```text
POST /books
```

| Body field | Required | Rule |
|---|---|---|
| `title` | Yes | Can't be empty |
| `author` | Yes | Can't be empty |
| `isbn` | Yes | 10 or 13 digits. Hyphens are allowed. |

```bash
curl -X POST http://localhost:8000/books -H "Content-Type: application/json" -d '{"title": "Dune", "author": "Frank Herbert", "isbn": "9780441013593"}'
```

**Response: 201**

```json
{"id": 6, "title": "Dune", "author": "Frank Herbert", "isbn": "9780441013593", "available": true}
```

| Error | Message | When |
|---|---|---|
| 400 | `title and author are required` | Either one is missing. |
| 400 | `invalid isbn` | The ISBN is missing or in the wrong format. |

### Delete a book

```text
DELETE /books/<id>
```

```bash
curl -X DELETE http://localhost:8000/books/6
```

**Response: 204**, with an empty body.

| Error | Message | When |
|---|---|---|
| 404 | `book not found` | The book doesn't exist. |
| 409 | `book is on loan` | The book is currently checked out. |

## Members

### List members

```text
GET /members
```

```bash
curl http://localhost:8000/members
```

**Response: 200**

```json
[
  {"id": 1, "name": "Sam Rivera", "email": "sam@campus.edu", "type": "student"},
  {"id": 2, "name": "Dr. Noor Aziz", "email": "noor@campus.edu", "type": "staff"},
  {"id": 3, "name": "Alex Chen", "email": "alex@campus.edu", "type": "student"}
]
```

### Get a member

```text
GET /members/<id>
```

```bash
curl http://localhost:8000/members/1
```

**Response: 200**

```json
{"id": 1, "name": "Sam Rivera", "email": "sam@campus.edu", "type": "student"}
```

| Error | Message | When |
|---|---|---|
| 404 | `member not found` | The member doesn't exist. |

### Add a member

```text
POST /members
```

| Body field | Required | Rule |
|---|---|---|
| `name` | Yes | Can't be empty |
| `email` | Yes | Must look like an email address, and can't already be registered |
| `type` | No | `student` or `staff`. If left out, it's `student`. |

```bash
curl -X POST http://localhost:8000/members -H "Content-Type: application/json" -d '{"name": "Lee Park", "email": "lee@campus.edu", "type": "staff"}'
```

**Response: 201**

```json
{"id": 4, "name": "Lee Park", "email": "lee@campus.edu", "type": "staff"}
```

| Error | Message | When |
|---|---|---|
| 400 | `name is required` | The name is missing. |
| 400 | `invalid email` | The email is missing or in the wrong format. |
| 400 | `type must be student or staff` | The type is anything else. |
| 409 | `email already registered` | Another member has that email. |

### Delete a member

```text
DELETE /members/<id>
```

```bash
curl -X DELETE http://localhost:8000/members/4
```

**Response: 204**, with an empty body. The member's past (returned and paid) loans are deleted with them.

| Error | Message | When |
|---|---|---|
| 404 | `member not found` | The member doesn't exist. |
| 409 | `member has books on loan` | The member still has a book checked out. |
| 409 | `member owes money` | The member has an unpaid fine. |

### Get a member's loans

```text
GET /members/<id>/loans
```

```bash
curl http://localhost:8000/members/3/loans
```

**Response: 200**

```json
{
  "loans": [
    {"id": 1, "book_id": 5, "due_date": "2026-10-31", "returned": false, "fine": 0.0, "fine_paid": false}
  ],
  "total_owed": 2.5,
  "loans_remaining": 2
}
```

`total_owed` adds up unpaid fines, including fines still building up on late books. `loans_remaining` is how many more books the member can check out.

| Error | Message | When |
|---|---|---|
| 404 | `member not found` | The member doesn't exist. |

## Loans

### List loans

```text
GET /loans
```

To list only overdue loans, use `GET /loans?overdue=true`.

```bash
curl http://localhost:8000/loans
```

**Response: 200**

```json
[
  {
    "id": 1,
    "book_id": 5,
    "member_id": 3,
    "due_date": "2026-10-31",
    "returned": false,
    "fine": 0.0,
    "fine_paid": false,
    "renewals": 0,
    "checked_out": "2026-10-17",
    "current_fine": 2.5
  }
]
```

### Get a loan

```text
GET /loans/<id>
```

```bash
curl http://localhost:8000/loans/1
```

**Response: 200**

```json
{
  "id": 1,
  "book_id": 5,
  "member_id": 3,
  "due_date": "2026-10-31",
  "returned": false,
  "fine": 0.0,
  "fine_paid": false,
  "renewals": 0,
  "checked_out": "2026-10-17",
  "current_fine": 2.5
}
```

| Error | Message | When |
|---|---|---|
| 404 | `loan not found` | The loan doesn't exist. |

### Check out a book

```text
POST /loans
```

| Body field | Required | Rule |
|---|---|---|
| `book_id` | Yes | The book's ID |
| `member_id` | Yes | The member's ID |
| `due_date` | No | A date in the form `YYYY-MM-DD`. If left out, it's 14 days from today. |

```bash
curl -X POST http://localhost:8000/loans -H "Content-Type: application/json" -d '{"book_id": 1, "member_id": 1}'
```

**Response: 201**

```json
{
  "id": 2,
  "book_id": 1,
  "member_id": 1,
  "due_date": "2026-11-19",
  "returned": false,
  "fine": 0.0,
  "fine_paid": false,
  "renewals": 0,
  "checked_out": "2026-11-05"
}
```

This also marks the book as unavailable and adds an email to `outbox.txt`.

| Error | Message | When |
|---|---|---|
| 400 | `book_id and member_id are required` | Either one is missing. |
| 400 | `invalid due_date` | The date is in the wrong format. |
| 404 | `book not found` | The book doesn't exist. |
| 404 | `member not found` | The member doesn't exist. |
| 409 | `book is not available` | The book is already checked out. |
| 409 | `member has unpaid fines` | The member owes money. |
| 409 | `loan limit reached` | A student has 3 open loans, or a staff member has 5. |

### Renew a loan

This adds 14 days to the due date. A loan can be renewed once. There is no request body.

```text
POST /loans/<id>/renew
```

```bash
curl -X POST http://localhost:8000/loans/2/renew
```

**Response: 200**

```json
{
  "id": 2,
  "book_id": 1,
  "member_id": 1,
  "due_date": "2026-12-03",
  "returned": false,
  "fine": 0.0,
  "fine_paid": false,
  "renewals": 1,
  "checked_out": "2026-11-05"
}
```

This also adds an email to `outbox.txt`.

| Error | Message | When |
|---|---|---|
| 404 | `loan not found` | The loan doesn't exist. |
| 409 | `loan already returned` | The book has come back. |
| 409 | `overdue loans cannot be renewed` | The due date has passed. |
| 409 | `loan was already renewed` | The loan has already had its one renewal. |

### Return a book

This calculates any fine at $0.50 per day late. There is no request body.

```text
POST /loans/<id>/return
```

```bash
curl -X POST http://localhost:8000/loans/1/return
```

**Response: 200**

```json
{
  "id": 1,
  "book_id": 5,
  "member_id": 3,
  "due_date": "2026-10-31",
  "returned": true,
  "fine": 2.5,
  "fine_paid": false,
  "renewals": 0,
  "checked_out": "2026-10-17"
}
```

This also marks the book as available and adds an email to `outbox.txt`.

| Error | Message | When |
|---|---|---|
| 404 | `loan not found` | The loan doesn't exist. |
| 409 | `loan already returned` | The book has already come back. |

### Pay a fine

The book must be returned first. There is no request body.

```text
POST /loans/<id>/pay-fine
```

```bash
curl -X POST http://localhost:8000/loans/1/pay-fine
```

**Response: 200**

```json
{
  "id": 1,
  "book_id": 5,
  "member_id": 3,
  "due_date": "2026-10-31",
  "returned": true,
  "fine": 2.5,
  "fine_paid": true,
  "renewals": 0,
  "checked_out": "2026-10-17"
}
```

This also adds an email to `outbox.txt`.

| Error | Message | When |
|---|---|---|
| 404 | `loan not found` | The loan doesn't exist. |
| 409 | `return the book before paying` | The book hasn't come back yet. |
| 409 | `no fine to pay` | There was no fine, or it's already paid. |

## Reports

These two examples show a **fresh database**, before any of the loan requests above.

### Overdue loans

```text
GET /reports/overdue
```

```bash
curl http://localhost:8000/reports/overdue
```

**Response: 200**

```json
{
  "items": [
    {"loan_id": 1, "title": "Code Complete", "member": "Alex Chen", "days_late": 5, "fine": 2.5}
  ],
  "total_fines": 2.5
}
```

### Library summary

```text
GET /reports/summary
```

```bash
curl http://localhost:8000/reports/summary
```

**Response: 200**

```json
{"total_books": 5, "on_loan": 1, "fines_outstanding": 2.5}
```

## Emails

The API doesn't send real email. It adds a line to `outbox.txt` instead, in this format:

```text
TO: sam@campus.edu | SUBJECT: Book checked out | BODY: You checked out Clean Code
```

| Request | Subject | Body |
|---|---|---|
| Check out a book | `Book checked out` | `You checked out <title>` |
| Renew a loan | `Loan renewed` | `You renewed <title>` |
| Return a book | `Book returned` | `You returned <title>. Fine: $<amount>` |
| Pay a fine | `Fine paid` | `We received $<amount>` |
