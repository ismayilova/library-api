from datetime import date

FINE_PER_DAY = 0.5

def days_late(due_date):
    return (date.today() - date.fromisoformat(due_date)).days

def calculate_fine(due_date):
    return max(0, days_late(due_date)) * FINE_PER_DAY


def calculate_balance(loans):
    owed = 0
    open_loans = 0
    for loan in loans:
        if loan[4] == 0:
            open_loans += 1
            late = days_late(loan[3])
            if late > 0:
                owed += late * FINE_PER_DAY
        elif loan[6] == 0:
            owed += loan[5]
    return owed, open_loans