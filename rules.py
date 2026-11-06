FINE_PER_DAY = 0.50

def fine_for_days(days):
    return max(0, days) * FINE_PER_DAY