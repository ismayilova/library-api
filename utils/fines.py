from datetime import date


def money(amount):
    return round(float(amount), 2)


def fine_for(due_date):
    days = (date.today() - date.fromisoformat(due_date)).days
    return money(max(0, days) * 0.50)


def amount_owed(loans):
    total = 0
    for loan in loans:
        if not loan[4]:
            total += fine_for(loan[3])
        elif not loan[6]:
            total += loan[5]
    return money(total)