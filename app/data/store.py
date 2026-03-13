"""
Shared in-memory data store — Customers, Products, and Orders.

Import this module as a singleton; all tools and resources share the same state.
Seed data is populated at import time and persists for the lifetime of the server process.
"""

from __future__ import annotations

from app.models.customer import Customer
from app.models.order import Order
from app.models.product import Product

customers: dict[str, Customer] = {}
products: dict[str, Product] = {}
orders: dict[str, Order] = {}


def _seed() -> None:
    # --- Customers ---
    for c in [
        Customer(
            id="cust-001",
            name="Alice Johnson",
            email="alice@example.com",
            phone="555-1001",
            created_at="2025-01-10T09:00:00Z",
        ),
        Customer(
            id="cust-002",
            name="Bob Smith",
            email="bob@example.com",
            phone="555-1002",
            created_at="2025-01-15T10:30:00Z",
        ),
        Customer(
            id="cust-003",
            name="Carol White",
            email="carol@example.com",
            phone="555-1003",
            created_at="2025-02-01T08:00:00Z",
        ),
    ]:
        customers[c.id] = c

    # --- Products ---
    for p in [
        Product(
            id="prod-001",
            name="Laptop Pro 15",
            description="High-performance laptop for professionals.",
            price=1299.99,
            stock=42,
            created_at="2025-01-05T08:00:00Z",
        ),
        Product(
            id="prod-002",
            name="Wireless Mouse",
            description="Ergonomic wireless mouse with long battery life.",
            price=29.99,
            stock=150,
            created_at="2025-01-06T09:00:00Z",
        ),
        Product(
            id="prod-003",
            name="USB-C Hub",
            description="7-in-1 USB-C hub with HDMI and power delivery.",
            price=49.99,
            stock=80,
            created_at="2025-01-07T10:00:00Z",
        ),
        Product(
            id="prod-004",
            name='Monitor 27"',
            description="4K IPS display with 144Hz refresh rate.",
            price=599.99,
            stock=20,
            created_at="2025-01-08T11:00:00Z",
        ),
        Product(
            id="prod-005",
            name="Mechanical Keyboard",
            description="TKL mechanical keyboard with Cherry MX switches.",
            price=89.99,
            stock=60,
            created_at="2025-01-09T12:00:00Z",
        ),
    ]:
        products[p.id] = p

    # --- Orders ---
    # Totals are pre-calculated from seed product prices.
    for o in [
        Order(
            id="order-001",
            customer_id="cust-001",
            product_ids=["prod-001", "prod-002"],
            status="delivered",
            total=1329.98,  # 1299.99 + 29.99
            created_at="2025-02-10T10:00:00Z",
        ),
        Order(
            id="order-002",
            customer_id="cust-002",
            product_ids=["prod-003", "prod-005"],
            status="shipped",
            total=139.98,  # 49.99 + 89.99
            created_at="2025-02-20T14:00:00Z",
        ),
        Order(
            id="order-003",
            customer_id="cust-001",
            product_ids=["prod-004"],
            status="confirmed",
            total=599.99,
            created_at="2025-03-01T09:00:00Z",
        ),
        Order(
            id="order-004",
            customer_id="cust-003",
            product_ids=["prod-002", "prod-003", "prod-005"],
            status="pending",
            total=169.97,  # 29.99 + 49.99 + 89.99
            created_at="2025-03-10T11:00:00Z",
        ),
    ]:
        orders[o.id] = o


_seed()
