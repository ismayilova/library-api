from dataclasses import dataclass


@dataclass
class Book:
    id: int
    title: str
    author: str
    isbn: str
    available: bool

    @classmethod
    def from_row(cls, row):
        if row is None:
            return None
        return cls(row["id"], row["title"], row["author"], row["isbn"], bool(row["available"]))
