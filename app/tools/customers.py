"""
Customer CRUD tools.

Exposes TOOL_DEFINITIONS (list) and handle(name, params) for dispatch by app/api/mcp.py.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

import app.data.store as store
from app.models.customer import Customer

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "create_customer",
        "description": "Create a new customer with a name, email, and phone number.",
        "inputSchema": {
            "type": "object",
            "required": ["name", "email", "phone"],
            "properties": {
                "name": {"type": "string", "description": "Full name of the customer."},
                "email": {"type": "string", "description": "Email address (must contain @)."},
                "phone": {"type": "string", "description": "Phone number."},
            },
        },
    },
    {
        "name": "update_customer",
        "description": "Update one or more fields on an existing customer.",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "string", "description": "Customer ID."},
                "name": {"type": "string", "description": "New name."},
                "email": {"type": "string", "description": "New email address."},
                "phone": {"type": "string", "description": "New phone number."},
            },
        },
    },
    {
        "name": "delete_customer",
        "description": "Delete a customer. Fails if the customer has any existing orders.",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "string", "description": "Customer ID to delete."},
            },
        },
    },
    {
        "name": "get_customer",
        "description": "Return a single customer by ID.",
        "inputSchema": {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "string", "description": "Customer ID."},
            },
        },
    },
    {
        "name": "list_customers",
        "description": "Return all customers.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]


def handle(name: str, params: dict[str, Any]) -> dict[str, Any]:
    dispatch = {
        "create_customer": _create_customer,
        "update_customer": _update_customer,
        "delete_customer": _delete_customer,
        "get_customer": _get_customer,
        "list_customers": _list_customers,
    }
    fn = dispatch.get(name)
    if fn is None:
        return _error(f"Unknown customer tool: {name}")
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


def _create_customer(params: dict) -> dict:
    name = (params.get("name") or "").strip()
    email = (params.get("email") or "").strip()
    phone = (params.get("phone") or "").strip()

    if not name:
        return _error("'name' is required.")
    if "@" not in email:
        return _error("'email' must contain '@'.")
    if not phone:
        return _error("'phone' is required.")

    cid = str(uuid.uuid4())
    customer = Customer(
        id=cid,
        name=name,
        email=email,
        phone=phone,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    store.customers[cid] = customer
    return _ok(customer.to_dict())


def _update_customer(params: dict) -> dict:
    cid = params.get("id", "")
    customer = store.customers.get(cid)
    if not customer:
        return _error(f"Customer '{cid}' not found.")
    if "name" in params:
        customer.name = params["name"]
    if "email" in params:
        if "@" not in params["email"]:
            return _error("'email' must contain '@'.")
        customer.email = params["email"]
    if "phone" in params:
        customer.phone = params["phone"]
    return _ok(customer.to_dict())


def _delete_customer(params: dict) -> dict:
    cid = params.get("id", "")
    if cid not in store.customers:
        return _error(f"Customer '{cid}' not found.")
    if any(o.customer_id == cid for o in store.orders.values()):
        return _error(
            f"Cannot delete customer '{cid}': they have existing orders. "
            "Delete or reassign those orders first."
        )
    del store.customers[cid]
    return _ok({"deleted": cid})


def _get_customer(params: dict) -> dict:
    cid = params.get("id", "")
    customer = store.customers.get(cid)
    if not customer:
        return _error(f"Customer '{cid}' not found.")
    return _ok(customer.to_dict())


def _list_customers(params: dict) -> dict:
    return _ok([c.to_dict() for c in store.customers.values()])
