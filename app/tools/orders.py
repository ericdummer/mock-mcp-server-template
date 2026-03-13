"""
Order CRUD tools.

Exposes TOOL_DEFINITIONS (list) and handle(name, params) for dispatch by app/api/mcp.py.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

import app.data.store as store
from app.models.order import Order

_ALLOWED_STATUSES = {"pending", "confirmed", "shipped", "delivered", "cancelled"}

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "create_order",
        "description": (
            "Create a new order for a customer. Validates that the customer and all "
            "products exist. Calculates total from current product prices."
        ),
        "inputSchema": {
            "type": "object",
            "required": ["customer_id", "product_ids"],
            "properties": {
                "customer_id": {"type": "string", "description": "ID of the customer placing the order."},
                "product_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of product IDs to include in the order.",
                },
            },
        },
    },
    {
        "name": "update_order_status",
        "description": "Update the status of an order.",
        "inputSchema": {
            "type": "object",
            "required": ["id", "status"],
            "properties": {
                "id": {"type": "string", "description": "Order ID."},
                "status": {
                    "type": "string",
                    "enum": ["pending", "confirmed", "shipped", "delivered", "cancelled"],
                    "description": "New status.",
                },
            },
        },
    },
    {
        "name": "add_products_to_order",
        "description": "Append one or more products to an existing order and recalculate total.",
        "inputSchema": {
            "type": "object",
            "required": ["id", "product_ids"],
            "properties": {
                "id": {"type": "string", "description": "Order ID."},
                "product_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Product IDs to add.",
                },
            },
        },
    },
    {
        "name": "remove_products_from_order",
        "description": "Remove one or more products from an existing order and recalculate total.",
        "inputSchema": {
            "type": "object",
            "required": ["id", "product_ids"],
            "properties": {
                "id": {"type": "string", "description": "Order ID."},
                "product_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Product IDs to remove.",
                },
            },
        },
    },
    {
        "name": "delete_order",
        "description": "Delete an order.",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "string", "description": "Order ID to delete."},
            },
        },
    },
    {
        "name": "get_order",
        "description": "Return a single order by ID.",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "string", "description": "Order ID."},
            },
        },
    },
    {
        "name": "list_orders",
        "description": "Return all orders.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "list_orders_by_customer",
        "description": "Return all orders for a given customer.",
        "inputSchema": {
            "type": "object",
            "required": ["customer_id"],
            "properties": {
                "customer_id": {"type": "string", "description": "Customer ID."},
            },
        },
    },
]


def handle(name: str, params: dict[str, Any]) -> dict[str, Any]:
    dispatch = {
        "create_order": _create_order,
        "update_order_status": _update_order_status,
        "add_products_to_order": _add_products_to_order,
        "remove_products_from_order": _remove_products_from_order,
        "delete_order": _delete_order,
        "get_order": _get_order,
        "list_orders": _list_orders,
        "list_orders_by_customer": _list_orders_by_customer,
    }
    fn = dispatch.get(name)
    if fn is None:
        return _error(f"Unknown order tool: {name}")
    return fn(params)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ok(data: Any) -> dict:
    return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}


def _error(msg: str) -> dict:
    return {
        "content": [{"type": "text", "text": json.dumps({"error": msg}, indent=2)}],
        "isError": True,
    }


def _calc_total(product_ids: list[str]) -> float:
    return sum(
        store.products[pid].price for pid in product_ids if pid in store.products
    )


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def _create_order(params: dict) -> dict:
    customer_id = params.get("customer_id", "")
    product_ids = params.get("product_ids") or []

    if customer_id not in store.customers:
        return _error(f"Customer '{customer_id}' not found.")
    if not product_ids:
        return _error("'product_ids' must not be empty.")
    missing = [pid for pid in product_ids if pid not in store.products]
    if missing:
        return _error(f"Products not found: {missing}")

    oid = str(uuid.uuid4())
    order = Order(
        id=oid,
        customer_id=customer_id,
        product_ids=list(product_ids),
        status="pending",
        total=_calc_total(product_ids),
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    store.orders[oid] = order
    return _ok(order.to_dict())


def _update_order_status(params: dict) -> dict:
    oid = params.get("id", "")
    status = params.get("status", "")
    order = store.orders.get(oid)
    if not order:
        return _error(f"Order '{oid}' not found.")
    if status not in _ALLOWED_STATUSES:
        return _error(
            f"Invalid status '{status}'. Must be one of: {sorted(_ALLOWED_STATUSES)}."
        )
    order.status = status
    return _ok(order.to_dict())


def _add_products_to_order(params: dict) -> dict:
    oid = params.get("id", "")
    product_ids = params.get("product_ids") or []
    order = store.orders.get(oid)
    if not order:
        return _error(f"Order '{oid}' not found.")
    missing = [pid for pid in product_ids if pid not in store.products]
    if missing:
        return _error(f"Products not found: {missing}")
    order.product_ids.extend(product_ids)
    order.total = _calc_total(order.product_ids)
    return _ok(order.to_dict())


def _remove_products_from_order(params: dict) -> dict:
    oid = params.get("id", "")
    product_ids = params.get("product_ids") or []
    order = store.orders.get(oid)
    if not order:
        return _error(f"Order '{oid}' not found.")
    missing = [pid for pid in product_ids if pid not in store.products]
    if missing:
        return _error(f"Products not found: {missing}")
    to_remove = set(product_ids)
    order.product_ids = [pid for pid in order.product_ids if pid not in to_remove]
    order.total = _calc_total(order.product_ids)
    return _ok(order.to_dict())


def _delete_order(params: dict) -> dict:
    oid = params.get("id", "")
    if oid not in store.orders:
        return _error(f"Order '{oid}' not found.")
    del store.orders[oid]
    return _ok({"deleted": oid})


def _get_order(params: dict) -> dict:
    oid = params.get("id", "")
    order = store.orders.get(oid)
    if not order:
        return _error(f"Order '{oid}' not found.")
    return _ok(order.to_dict())


def _list_orders(params: dict) -> dict:
    return _ok([o.to_dict() for o in store.orders.values()])


def _list_orders_by_customer(params: dict) -> dict:
    customer_id = params.get("customer_id", "")
    if customer_id not in store.customers:
        return _error(f"Customer '{customer_id}' not found.")
    result = [
        o.to_dict() for o in store.orders.values() if o.customer_id == customer_id
    ]
    return _ok(result)
