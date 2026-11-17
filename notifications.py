# Fake notifications for testing. No real emails are sent.
def notify(email, subject, body):
    with open("outbox.txt", "a") as file:
        file.write("TO: " + email + " | SUBJECT: " + subject + " | BODY: " + body + "\n")