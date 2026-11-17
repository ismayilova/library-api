from dataclasses import dataclass


@dataclass
class Loan:
    id: int
    book_id: int
    member_id: int
    due_date: str
    returned: bool
    fine: float
    fine_paid: bool
    renewals: int
    checked_out: str

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(
            row["id"],
            row["book_id"],
            row["member_id"],
            row["due_date"],
            bool(row["returned"]),
            row["fine"],
            bool(row["fine_paid"]),
            row["renewals"],
            row["checked_out"],
        )
