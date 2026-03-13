"""Order data model."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class Order:
    id: str
    customer_id: str
    product_ids: list[str]
    status: str
    total: float
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)
