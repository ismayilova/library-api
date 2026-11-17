from dataclasses import dataclass


@dataclass
class Member:
    id: int
    name: str
    email: str
    type: str

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(row["id"], row["name"], row["email"], row["type"])
