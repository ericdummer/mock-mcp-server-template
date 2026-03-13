"""
Product CRUD tools.

Exposes TOOL_DEFINITIONS (list) and handle(name, params) for dispatch by app/api/mcp.py.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

import app.data.store as store
from app.models.product import Product

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "create_product",
        "description": "Create a new product in the catalog.",
        "inputSchema": {
            "type": "object",
            "required": ["name", "description", "price", "stock"],
            "properties": {
                "name": {"type": "string", "description": "Product name."},
                "description": {
                    "type": "string",
                    "description": "Product description.",
                },
                "price": {
                    "type": "number",
                    "description": "Unit price (non-negative).",
                },
                "stock": {
                    "type": "integer",
                    "description": "Stock quantity (non-negative).",
                },
            },
        },
    },
    {
        "name": "update_product",
        "description": "Update one or more fields on an existing product.",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "string", "description": "Product ID."},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "price": {"type": "number"},
                "stock": {"type": "integer"},
            },
        },
    },
    {
        "name": "delete_product",
        "description": "Delete a product. Fails if it is referenced in any existing order.",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "string", "description": "Product ID to delete."},
            },
        },
    },
    {
        "name": "get_product",
        "description": "Return a single product by ID.",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "string", "description": "Product ID."},
            },
        },
    },
    {
        "name": "list_products",
        "description": "Return all products.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]


def handle(name: str, params: dict[str, Any]) -> dict[str, Any]:
    dispatch = {
        "create_product": _create_product,
        "update_product": _update_product,
        "delete_product": _delete_product,
        "get_product": _get_product,
        "list_products": _list_products,
    }
    fn = dispatch.get(name)
    if fn is None:
        return _error(f"Unknown product tool: {name}")
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


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def _create_product(params: dict) -> dict:
    name = (params.get("name") or "").strip()
    description = (params.get("description") or "").strip()
    price = params.get("price")
    stock = params.get("stock")

    if not name:
        return _error("'name' is required.")
    if price is None or float(price) < 0:
        return _error("'price' must be a non-negative number.")
    if stock is None or int(stock) < 0:
        return _error("'stock' must be a non-negative integer.")

    pid = str(uuid.uuid4())
    product = Product(
        id=pid,
        name=name,
        description=description,
        price=float(price),
        stock=int(stock),
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    store.products[pid] = product
    return _ok(product.to_dict())


def _update_product(params: dict) -> dict:
    pid = params.get("id", "")
    product = store.products.get(pid)
    if not product:
        return _error(f"Product '{pid}' not found.")
    if "name" in params:
        product.name = params["name"]
    if "description" in params:
        product.description = params["description"]
    if "price" in params:
        product.price = float(params["price"])
    if "stock" in params:
        product.stock = int(params["stock"])
    return _ok(product.to_dict())


def _delete_product(params: dict) -> dict:
    pid = params.get("id", "")
    if pid not in store.products:
        return _error(f"Product '{pid}' not found.")
    if any(pid in o.product_ids for o in store.orders.values()):
        return _error(
            f"Cannot delete product '{pid}': it is referenced in one or more orders. "
            "Remove it from those orders first."
        )
    del store.products[pid]
    return _ok({"deleted": pid})


def _get_product(params: dict) -> dict:
    pid = params.get("id", "")
    product = store.products.get(pid)
    if not product:
        return _error(f"Product '{pid}' not found.")
    return _ok(product.to_dict())


def _list_products(params: dict) -> dict:
    return _ok([p.to_dict() for p in store.products.values()])
