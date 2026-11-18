import os
import tempfile
import unittest
from datetime import date, timedelta

import notifications
from errors import LibraryError, api_error
from utils import checks, fines, validation


def days_ago(n):
    return (date.today() - timedelta(days=n)).isoformat()


def make_loan(**overrides):
    loan = {"returned": 0, "due_date": days_ago(0), "fine": 0, "fine_paid": 0, "renewals": 0}
    loan.update(overrides)
    return loan


class ErrorsTest(unittest.TestCase):
    def test_api_error_keeps_message_and_status(self):
        error = api_error("custom message", 418)
        self.assertIsInstance(error, LibraryError)
        self.assertEqual(error.message, "custom message")
        self.assertEqual(error.status_code, 418)


class FinesTest(unittest.TestCase):
    def test_fine_is_fifty_cents_per_day_late(self):
        self.assertEqual(fines.fine_for(days_ago(4)), 2.0)

    def test_no_fine_when_on_time_or_early(self):
        self.assertEqual(fines.fine_for(days_ago(0)), 0)
        self.assertEqual(fines.fine_for(days_ago(-3)), 0)

    def test_amount_owed(self):
        self.assertEqual(fines.amount_owed(make_loan(due_date=days_ago(5))), 2.5)
        self.assertEqual(fines.amount_owed(make_loan(returned=1, fine=1.5)), 1.5)
        self.assertEqual(fines.amount_owed(make_loan(returned=1, fine=1.5, fine_paid=1)), 0)

    def test_total_owed_adds_all_loans(self):
        loans = [make_loan(due_date=days_ago(2)), make_loan(returned=1, fine=3.0)]
        self.assertEqual(fines.total_owed(loans), 4.0)


class ChecksTest(unittest.TestCase):
    def test_overdue_only_when_open_and_past_due(self):
        self.assertTrue(checks.is_overdue(make_loan(due_date=days_ago(1))))
        self.assertFalse(checks.is_overdue(make_loan(due_date=days_ago(0))))
        self.assertFalse(checks.is_overdue(make_loan(due_date=days_ago(9), returned=1)))

    def test_loan_limits(self):
        student, staff = {"type": "student"}, {"type": "staff"}
        three_open = [make_loan() for _ in range(3)]
        self.assertTrue(checks.has_reached_loan_limit(student, three_open))
        self.assertFalse(checks.has_reached_loan_limit(staff, three_open))
        self.assertEqual(checks.loans_remaining(staff, three_open), 2)

    def test_renewals_and_fines_to_pay(self):
        self.assertTrue(checks.has_renewals_left(make_loan(renewals=0)))
        self.assertFalse(checks.has_renewals_left(make_loan(renewals=1)))
        self.assertTrue(checks.has_fine_to_pay(make_loan(returned=1, fine=1.0)))
        self.assertFalse(checks.has_fine_to_pay(make_loan(returned=1, fine=1.0, fine_paid=1)))


class ValidationTest(unittest.TestCase):
    def test_validators(self):
        self.assertTrue(validation.is_valid_isbn("978-0-441-01359-3"))
        self.assertFalse(validation.is_valid_isbn("123"))
        self.assertTrue(validation.is_valid_email("a@b.co"))
        self.assertFalse(validation.is_valid_email("nope"))
        self.assertTrue(validation.is_valid_date("2026-01-31"))
        self.assertFalse(validation.is_valid_date("31/01/2026"))
        self.assertTrue(validation.is_valid_member_type("staff"))
        self.assertFalse(validation.is_valid_member_type("guest"))


class MockNotificationsTest(unittest.TestCase):
    def setUp(self):
        self.original = notifications.get_sender()
        self.folder = tempfile.TemporaryDirectory()
        self.mock = notifications.MockEmailSender(os.path.join(self.folder.name, "outbox.txt"))
        notifications.set_sender(self.mock)

    def tearDown(self):
        notifications.set_sender(self.original)
        self.folder.cleanup()

    def test_mock_records_what_was_sent_and_sends_nothing_real(self):
        notifications.send_email("sam@campus.edu", "Hello", "Body text")
        self.assertEqual(self.mock.sent, [{"to": "sam@campus.edu", "subject": "Hello", "body": "Body text"}])
        with open(self.mock.outbox_path) as f:
            self.assertEqual(f.read(), "TO: sam@campus.edu | SUBJECT: Hello | BODY: Body text\n")


if __name__ == "__main__":
    unittest.main()
