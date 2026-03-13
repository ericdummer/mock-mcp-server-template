"""Product data model."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class Product:
    id: str
    name: str
    description: str
    price: float
    stock: int
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)
