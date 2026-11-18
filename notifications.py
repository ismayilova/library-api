"""Notifications.

The library does not send real email. `MockEmailSender` is a mock object (see
https://en.wikipedia.org/wiki/Mock_object): it stands in for a real mail server,
and it remembers what it was asked to send so that tests can check it.

It also appends each message to `outbox.txt`, because the API documents that file
as the place where "sent" emails show up.

To use a real mail server later, write another class with the same `send(...)`
method and pass it to `set_sender(...)`. Nothing else has to change.
"""

OUTBOX_PATH = "outbox.txt"


class MockEmailSender:
    def __init__(self, outbox_path=OUTBOX_PATH):
        self.outbox_path = outbox_path
        self.sent = []  # every message "sent", oldest first

    def send(self, email, subject, body):
        self.sent.append({"to": email, "subject": subject, "body": body})
        with open(self.outbox_path, "a") as f:
            f.write("TO: " + email + " | SUBJECT: " + subject + " | BODY: " + body + "\n")


_sender = MockEmailSender()


def set_sender(sender):
    """Replace the sender (for example with a real one, or a different mock in a test)."""
    global _sender
    _sender = sender


def get_sender():
    return _sender


def send_email(email, subject, body):
    _sender.send(email, subject, body)
