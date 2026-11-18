from helpers.validators import money

def _write(email, subject, body):
    with open("outbox.txt", "a") as f:
        f.write("TO: " + email + " | SUBJECT: " + subject + " | BODY: " + body + "\n")

def notify(kind, title, email, send=True):
    if not send:
        return
    if kind == "checkout":
        subject = "Book checked out"
        body = "You checked out " + title
    elif kind == "renew":
        subject = "Loan renewed"
        body = "You renewed " + title
    else:
        subject = "Library notice"
        body = title
    _write(email, subject, body)

def notify_return(email, title, fine):
    _write(email, "Book returned", "You returned " + title + ". Fine: $" + str(money(fine)))

def notify_fine_paid(email, amount):
    _write(email, "Fine paid", "We received $" + str(money(amount)))