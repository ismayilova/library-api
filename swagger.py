"""OpenAPI spec and Swagger UI for the Library API.

Serves the spec at /openapi.json and the interactive UI at /docs.
Swagger UI assets are loaded from a CDN, so no extra Python dependency is needed.
"""
from flask import Blueprint, jsonify

swagger_bp = Blueprint("swagger", __name__)


def _ref(name):
    return {"$ref": "#/components/schemas/" + name}


def _json(schema, description):
    return {"description": description, "content": {"application/json": {"schema": schema}}}


def _error(description):
    return _json(_ref("Error"), description)


def _id_param(name, description):
    return {"name": name, "in": "path", "required": True, "description": description, "schema": {"type": "integer"}}


def _body(schema_name):
    return {"required": True, "content": {"application/json": {"schema": _ref(schema_name)}}}


LOAN_ID = _id_param("loan_id", "Loan ID")
BOOK_ID = _id_param("book_id", "Book ID")
MEMBER_ID = _id_param("member_id", "Member ID")

SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "Campus Library API",
        "version": "1.0.0",
        "description": (
            "Books, members, loans and reports for a campus library.\n\n"
            "**Rules:** loans last 14 days and can be renewed once (if not overdue); "
            "late returns cost $0.50/day; students may hold 3 open loans, staff 5; "
            "members who owe money can't check out books."
        ),
    },
    "tags": [
        {"name": "Books"},
        {"name": "Members"},
        {"name": "Loans"},
        {"name": "Reports"},
    ],
    "paths": {
        "/books": {
            "get": {
                "tags": ["Books"],
                "summary": "List books",
                "parameters": [
                    {
                        "name": "available",
                        "in": "query",
                        "required": False,
                        "description": "Set to `true` to list only available books",
                        "schema": {"type": "string", "enum": ["true"]},
                    }
                ],
                "responses": {"200": _json({"type": "array", "items": _ref("Book")}, "List of books")},
            },
            "post": {
                "tags": ["Books"],
                "summary": "Add a book",
                "requestBody": _body("NewBook"),
                "responses": {
                    "201": _json(_ref("Book"), "Book created"),
                    "400": _error("Missing title/author or invalid ISBN"),
                },
            },
        },
        "/books/{book_id}": {
            "parameters": [BOOK_ID],
            "get": {
                "tags": ["Books"],
                "summary": "Get a book",
                "responses": {"200": _json(_ref("Book"), "The book"), "404": _error("Book not found")},
            },
            "delete": {
                "tags": ["Books"],
                "summary": "Delete a book that isn't on loan",
                "responses": {
                    "204": {"description": "Book deleted"},
                    "404": _error("Book not found"),
                    "409": _error("Book is on loan"),
                },
            },
        },
        "/members": {
            "get": {
                "tags": ["Members"],
                "summary": "List members",
                "responses": {"200": _json({"type": "array", "items": _ref("Member")}, "List of members")},
            },
            "post": {
                "tags": ["Members"],
                "summary": "Add a member",
                "requestBody": _body("NewMember"),
                "responses": {
                    "201": _json(_ref("Member"), "Member created"),
                    "400": _error("Missing name, invalid email or invalid type"),
                    "409": _error("Email already registered"),
                },
            },
        },
        "/members/{member_id}": {
            "parameters": [MEMBER_ID],
            "get": {
                "tags": ["Members"],
                "summary": "Get a member",
                "responses": {"200": _json(_ref("Member"), "The member"), "404": _error("Member not found")},
            },
        },
        "/members/{member_id}/loans": {
            "parameters": [MEMBER_ID],
            "get": {
                "tags": ["Members"],
                "summary": "Get a member's loans and amount owed",
                "responses": {
                    "200": _json(_ref("MemberLoans"), "The member's loans"),
                    "404": _error("Member not found"),
                },
            },
        },
        "/loans": {
            "get": {
                "tags": ["Loans"],
                "summary": "List loans",
                "parameters": [
                    {
                        "name": "overdue",
                        "in": "query",
                        "required": False,
                        "description": "Set to `true` to list only open, overdue loans",
                        "schema": {"type": "string", "enum": ["true"]},
                    }
                ],
                "responses": {
                    "200": _json({"type": "array", "items": _ref("LoanWithCurrentFine")}, "List of loans")
                },
            },
            "post": {
                "tags": ["Loans"],
                "summary": "Check out a book",
                "requestBody": _body("NewLoan"),
                "responses": {
                    "201": _json(_ref("Loan"), "Loan created"),
                    "400": _error("Missing book_id/member_id or invalid due_date"),
                    "404": _error("Book or member not found"),
                    "409": _error("Book not available, unpaid fines, or loan limit reached"),
                },
            },
        },
        "/loans/{loan_id}": {
            "parameters": [LOAN_ID],
            "get": {
                "tags": ["Loans"],
                "summary": "Get a loan",
                "responses": {
                    "200": _json(_ref("LoanWithCurrentFine"), "The loan"),
                    "404": _error("Loan not found"),
                },
            },
        },
        "/loans/{loan_id}/return": {
            "parameters": [LOAN_ID],
            "post": {
                "tags": ["Loans"],
                "summary": "Return a book",
                "responses": {
                    "200": _json(_ref("Loan"), "Loan returned; fine calculated"),
                    "404": _error("Loan not found"),
                    "409": _error("Loan already returned"),
                },
            },
        },
        "/loans/{loan_id}/renew": {
            "parameters": [LOAN_ID],
            "post": {
                "tags": ["Loans"],
                "summary": "Renew a loan for 14 more days",
                "responses": {
                    "200": _json(_ref("Loan"), "Loan renewed"),
                    "404": _error("Loan not found"),
                    "409": _error("Already returned, overdue, or already renewed"),
                },
            },
        },
        "/loans/{loan_id}/pay-fine": {
            "parameters": [LOAN_ID],
            "post": {
                "tags": ["Loans"],
                "summary": "Pay a fine",
                "responses": {
                    "200": _json(_ref("Loan"), "Fine paid"),
                    "404": _error("Loan not found"),
                    "409": _error("Book not returned yet, or no fine to pay"),
                },
            },
        },
        "/reports/overdue": {
            "get": {
                "tags": ["Reports"],
                "summary": "List overdue loans",
                "responses": {"200": _json(_ref("OverdueReport"), "Overdue loans and total fines")},
            },
        },
        "/reports/summary": {
            "get": {
                "tags": ["Reports"],
                "summary": "Get library totals",
                "responses": {"200": _json(_ref("SummaryReport"), "Library totals")},
            },
        },
    },
    "components": {
        "schemas": {
            "Error": {
                "type": "object",
                "properties": {"error": {"type": "string", "example": "book not found"}},
            },
            "Book": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "title": {"type": "string", "example": "Clean Code"},
                    "author": {"type": "string", "example": "Robert C. Martin"},
                    "isbn": {"type": "string", "example": "9780132350884"},
                    "available": {"type": "boolean", "example": True},
                },
            },
            "NewBook": {
                "type": "object",
                "required": ["title", "author", "isbn"],
                "properties": {
                    "title": {"type": "string", "example": "Domain-Driven Design"},
                    "author": {"type": "string", "example": "Eric Evans"},
                    "isbn": {"type": "string", "description": "10 or 13 digits; dashes allowed", "example": "9780321125217"},
                },
            },
            "Member": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "name": {"type": "string", "example": "Sam Rivera"},
                    "email": {"type": "string", "format": "email", "example": "sam@campus.edu"},
                    "type": {"type": "string", "enum": ["student", "staff"]},
                },
            },
            "NewMember": {
                "type": "object",
                "required": ["name", "email"],
                "properties": {
                    "name": {"type": "string", "example": "Jordan Lee"},
                    "email": {"type": "string", "format": "email", "example": "jordan@campus.edu"},
                    "type": {"type": "string", "enum": ["student", "staff"], "default": "student"},
                },
            },
            "Loan": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 2},
                    "book_id": {"type": "integer", "example": 1},
                    "member_id": {"type": "integer", "example": 1},
                    "due_date": {"type": "string", "format": "date"},
                    "returned": {"type": "boolean"},
                    "fine": {"type": "number", "format": "float", "example": 0.0},
                    "fine_paid": {"type": "boolean"},
                    "renewals": {"type": "integer", "example": 0},
                    "checked_out": {"type": "string", "format": "date"},
                },
            },
            "LoanWithCurrentFine": {
                "allOf": [
                    _ref("Loan"),
                    {
                        "type": "object",
                        "properties": {
                            "current_fine": {
                                "type": "number",
                                "format": "float",
                                "description": "Fine accrued so far for open loans; stored fine for returned ones",
                            }
                        },
                    },
                ]
            },
            "NewLoan": {
                "type": "object",
                "required": ["book_id", "member_id"],
                "properties": {
                    "book_id": {"type": "integer", "example": 1},
                    "member_id": {"type": "integer", "example": 1},
                    "due_date": {"type": "string", "format": "date", "description": "Defaults to 14 days from today"},
                },
            },
            "MemberLoan": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "book_id": {"type": "integer"},
                    "due_date": {"type": "string", "format": "date"},
                    "returned": {"type": "boolean"},
                    "fine": {"type": "number", "format": "float"},
                    "fine_paid": {"type": "boolean"},
                },
            },
            "MemberLoans": {
                "type": "object",
                "properties": {
                    "loans": {"type": "array", "items": _ref("MemberLoan")},
                    "total_owed": {"type": "number", "format": "float"},
                    "loans_remaining": {"type": "integer"},
                },
            },
            "OverdueReport": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "loan_id": {"type": "integer"},
                                "title": {"type": "string"},
                                "member": {"type": "string"},
                                "days_late": {"type": "integer"},
                                "fine": {"type": "number", "format": "float"},
                            },
                        },
                    },
                    "total_fines": {"type": "number", "format": "float"},
                },
            },
            "SummaryReport": {
                "type": "object",
                "properties": {
                    "total_books": {"type": "integer"},
                    "on_loan": {"type": "integer"},
                    "fines_outstanding": {"type": "number", "format": "float"},
                },
            },
        }
    },
}

SWAGGER_UI_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Campus Library API - Swagger UI</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui-bundle.js"></script>
  <script>
    window.ui = SwaggerUIBundle({ url: "/openapi.json", dom_id: "#swagger-ui" });
  </script>
</body>
</html>
"""


@swagger_bp.route("/openapi.json", methods=["GET"])
def openapi_spec():
    return jsonify(SPEC)


@swagger_bp.route("/docs", methods=["GET"])
def swagger_ui():
    return SWAGGER_UI_HTML
