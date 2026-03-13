"""Customer data model."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class Customer:
    id: str
    name: str
    email: str
    phone: str
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)
