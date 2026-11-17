"""Tests for the Library API. Do not change this file.

The tests only use the HTTP endpoints, so they keep working however you
organize the code. Each test runs in its own temporary folder with fresh data.
"""
import os
import tempfile
import unittest
from datetime import date, timedelta

from app import app, init_db


def days_from_today(days):
    return (date.today() + timedelta(days=days)).isoformat()


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.original_dir = os.getcwd()
        self.temp_dir = tempfile.TemporaryDirectory()
        os.chdir(self.temp_dir.name)
        init_db()
        self.client = app.test_client()

    def tearDown(self):
        os.chdir(self.original_dir)
        self.temp_dir.cleanup()

    def checkout(self, book_id=1, member_id=1, due_date=None):
        body = {"book_id": book_id, "member_id": member_id}
        if due_date:
            body["due_date"] = due_date
        return self.client.post("/loans", json=body)

    def outbox(self):
        if not os.path.exists("outbox.txt"):
            return ""
        with open("outbox.txt") as f:
            return f.read()


class BookTests(ApiTestCase):
    def test_list_books(self):
        response = self.client.get("/books")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 5)

    def test_list_only_available_books(self):
        response = self.client.get("/books?available=true")
        titles = [book["title"] for book in response.get_json()]
        self.assertEqual(len(titles), 4)
        self.assertNotIn("Code Complete", titles)

    def test_get_book(self):
        response = self.client.get("/books/1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {
                "id": 1,
                "title": "Clean Code",
                "author": "Robert C. Martin",
                "isbn": "9780132350884",
                "available": True,
            },
        )

    def test_get_missing_book(self):
        self.assertEqual(self.client.get("/books/999").status_code, 404)

    def test_create_book(self):
        response = self.client.post(
            "/books", json={"title": "Dune", "author": "Frank Herbert", "isbn": "978-0441013593"}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["id"], 6)
        self.assertTrue(response.get_json()["available"])

    def test_create_book_requires_title_and_author(self):
        response = self.client.post("/books", json={"isbn": "9780441013593"})
        self.assertEqual(response.status_code, 400)

    def test_create_book_rejects_bad_isbn(self):
        response = self.client.post("/books", json={"title": "Dune", "author": "Frank Herbert", "isbn": "123"})
        self.assertEqual(response.status_code, 400)

    def test_delete_book(self):
        self.assertEqual(self.client.delete("/books/1").status_code, 204)
        self.assertEqual(self.client.get("/books/1").status_code, 404)

    def test_delete_missing_book(self):
        self.assertEqual(self.client.delete("/books/999").status_code, 404)

    def test_cannot_delete_book_on_loan(self):
        self.assertEqual(self.client.delete("/books/5").status_code, 409)


class MemberTests(ApiTestCase):
    def test_list_members(self):
        self.assertEqual(len(self.client.get("/members").get_json()), 3)

    def test_get_member(self):
        self.assertEqual(
            self.client.get("/members/2").get_json(),
            {"id": 2, "name": "Dr. Noor Aziz", "email": "noor@campus.edu", "type": "staff"},
        )

    def test_get_missing_member(self):
        self.assertEqual(self.client.get("/members/999").status_code, 404)

    def test_create_member_defaults_to_student(self):
        response = self.client.post("/members", json={"name": "Kim", "email": "kim@campus.edu"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["type"], "student")

    def test_create_member_requires_name(self):
        response = self.client.post("/members", json={"email": "kim@campus.edu"})
        self.assertEqual(response.status_code, 400)

    def test_create_member_rejects_bad_email(self):
        response = self.client.post("/members", json={"name": "Kim", "email": "not-an-email"})
        self.assertEqual(response.status_code, 400)

    def test_create_member_rejects_bad_type(self):
        response = self.client.post("/members", json={"name": "Kim", "email": "kim@campus.edu", "type": "alien"})
        self.assertEqual(response.status_code, 400)

    def test_create_member_rejects_duplicate_email(self):
        response = self.client.post("/members", json={"name": "Sam 2", "email": "sam@campus.edu"})
        self.assertEqual(response.status_code, 409)

    def test_member_loans_shows_amount_owed(self):
        body = self.client.get("/members/3/loans").get_json()
        self.assertEqual(len(body["loans"]), 1)
        self.assertEqual(body["total_owed"], 2.5)
        self.assertEqual(body["loans_remaining"], 2)

    def test_staff_can_borrow_more(self):
        self.assertEqual(self.client.get("/members/2/loans").get_json()["loans_remaining"], 5)

    def test_missing_member_loans(self):
        self.assertEqual(self.client.get("/members/999/loans").status_code, 404)

    def test_delete_member(self):
        self.assertEqual(self.client.delete("/members/1").status_code, 204)
        self.assertEqual(self.client.get("/members/1").status_code, 404)

    def test_delete_missing_member(self):
        self.assertEqual(self.client.delete("/members/999").status_code, 404)

    def test_cannot_delete_member_with_open_loan(self):
        response = self.client.delete("/members/3")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["error"], "member has books on loan")

    def test_cannot_delete_member_who_owes_money(self):
        self.client.post("/loans/1/return")
        response = self.client.delete("/members/3")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["error"], "member owes money")

    def test_delete_member_removes_their_paid_loans(self):
        self.client.post("/loans/1/return")
        self.client.post("/loans/1/pay-fine")
        self.assertEqual(self.client.delete("/members/3").status_code, 204)
        self.assertEqual(self.client.get("/loans/1").status_code, 404)


class CheckoutTests(ApiTestCase):
    def test_checkout_sets_due_date_and_marks_book_unavailable(self):
        response = self.checkout()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["due_date"], days_from_today(14))
        self.assertEqual(response.get_json()["checked_out"], days_from_today(0))
        self.assertFalse(self.client.get("/books/1").get_json()["available"])

    def test_checkout_sends_email(self):
        self.checkout()
        self.assertIn("TO: sam@campus.edu | SUBJECT: Book checked out", self.outbox())

    def test_checkout_requires_book_and_member(self):
        self.assertEqual(self.client.post("/loans", json={"book_id": 1}).status_code, 400)

    def test_checkout_rejects_bad_due_date(self):
        self.assertEqual(self.checkout(due_date="next week").status_code, 400)

    def test_checkout_missing_book(self):
        self.assertEqual(self.checkout(book_id=999).status_code, 404)

    def test_checkout_missing_member(self):
        self.assertEqual(self.checkout(member_id=999).status_code, 404)

    def test_checkout_unavailable_book(self):
        self.assertEqual(self.checkout(book_id=5).status_code, 409)

    def test_member_with_overdue_loan_cannot_checkout(self):
        response = self.checkout(member_id=3)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["error"], "member has unpaid fines")

    def test_student_limit_is_three(self):
        for book_id in (1, 2, 3):
            self.assertEqual(self.checkout(book_id=book_id).status_code, 201)
        response = self.checkout(book_id=4)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["error"], "loan limit reached")

    def test_staff_can_exceed_student_limit(self):
        for book_id in (1, 2, 3, 4):
            self.assertEqual(self.checkout(book_id=book_id, member_id=2).status_code, 201)


class LoanTests(ApiTestCase):
    def test_get_loan_shows_current_fine(self):
        body = self.client.get("/loans/1").get_json()
        self.assertEqual(body["current_fine"], 2.5)
        self.assertEqual(body["fine"], 0)

    def test_get_missing_loan(self):
        self.assertEqual(self.client.get("/loans/999").status_code, 404)

    def test_list_loans(self):
        self.checkout()
        self.assertEqual(len(self.client.get("/loans").get_json()), 2)

    def test_list_overdue_loans(self):
        self.checkout()
        body = self.client.get("/loans?overdue=true").get_json()
        self.assertEqual([loan["id"] for loan in body], [1])


class ReturnTests(ApiTestCase):
    def test_on_time_return_has_no_fine(self):
        self.checkout()
        response = self.client.post("/loans/2/return")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["returned"])
        self.assertEqual(response.get_json()["fine"], 0)
        self.assertTrue(self.client.get("/books/1").get_json()["available"])

    def test_late_return_charges_fifty_cents_per_day(self):
        self.checkout(due_date=days_from_today(-4))
        self.assertEqual(self.client.post("/loans/2/return").get_json()["fine"], 2.0)

    def test_return_sends_email_with_fine(self):
        self.client.post("/loans/1/return")
        self.assertIn(
            "TO: alex@campus.edu | SUBJECT: Book returned | BODY: You returned Code Complete. Fine: $2.5",
            self.outbox(),
        )

    def test_return_missing_loan(self):
        self.assertEqual(self.client.post("/loans/999/return").status_code, 404)

    def test_cannot_return_twice(self):
        self.client.post("/loans/1/return")
        self.assertEqual(self.client.post("/loans/1/return").status_code, 409)


class RenewTests(ApiTestCase):
    def test_renew_adds_fourteen_days_to_due_date(self):
        self.checkout()
        response = self.client.post("/loans/2/renew")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["due_date"], days_from_today(28))
        self.assertEqual(response.get_json()["renewals"], 1)
        self.assertIn("SUBJECT: Loan renewed", self.outbox())

    def test_can_renew_only_once(self):
        self.checkout()
        self.client.post("/loans/2/renew")
        self.assertEqual(self.client.post("/loans/2/renew").status_code, 409)

    def test_cannot_renew_overdue_loan(self):
        self.assertEqual(self.client.post("/loans/1/renew").status_code, 409)

    def test_cannot_renew_returned_loan(self):
        self.checkout()
        self.client.post("/loans/2/return")
        self.assertEqual(self.client.post("/loans/2/renew").status_code, 409)

    def test_renew_missing_loan(self):
        self.assertEqual(self.client.post("/loans/999/renew").status_code, 404)


class PayFineTests(ApiTestCase):
    def test_pay_fine_clears_debt(self):
        self.client.post("/loans/1/return")
        self.assertEqual(self.client.get("/members/3/loans").get_json()["total_owed"], 2.5)
        response = self.client.post("/loans/1/pay-fine")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["fine_paid"])
        self.assertEqual(self.client.get("/members/3/loans").get_json()["total_owed"], 0)
        self.assertIn("SUBJECT: Fine paid | BODY: We received $2.5", self.outbox())

    def test_member_can_checkout_after_paying(self):
        self.client.post("/loans/1/return")
        self.assertEqual(self.checkout(member_id=3).status_code, 409)
        self.client.post("/loans/1/pay-fine")
        self.assertEqual(self.checkout(member_id=3).status_code, 201)

    def test_must_return_before_paying(self):
        self.assertEqual(self.client.post("/loans/1/pay-fine").status_code, 409)

    def test_cannot_pay_when_no_fine(self):
        self.checkout()
        self.client.post("/loans/2/return")
        self.assertEqual(self.client.post("/loans/2/pay-fine").status_code, 409)

    def test_cannot_pay_twice(self):
        self.client.post("/loans/1/return")
        self.client.post("/loans/1/pay-fine")
        self.assertEqual(self.client.post("/loans/1/pay-fine").status_code, 409)

    def test_pay_missing_loan(self):
        self.assertEqual(self.client.post("/loans/999/pay-fine").status_code, 404)


class ReportTests(ApiTestCase):
    def test_overdue_report(self):
        self.assertEqual(
            self.client.get("/reports/overdue").get_json(),
            {
                "items": [
                    {"loan_id": 1, "title": "Code Complete", "member": "Alex Chen", "days_late": 5, "fine": 2.5}
                ],
                "total_fines": 2.5,
            },
        )

    def test_summary_report(self):
        self.checkout()
        self.assertEqual(
            self.client.get("/reports/summary").get_json(),
            {"total_books": 5, "on_loan": 2, "fines_outstanding": 2.5},
        )


if __name__ == "__main__":
    unittest.main()
