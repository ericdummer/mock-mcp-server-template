"""
Customer resources — read-only MCP resource handlers.

Concrete resources:
  customers://all           — all customers as JSON array

Resource templates:
  customers://{id}          — single customer by ID
  customers://{id}/orders   — all orders for a customer
"""

from __future__ import annotations

import json
import re

from mcp.types import Resource, ResourceTemplate

import app.data.store as store

_SCHEME = "customers"


def get_resources() -> list[Resource]:
    return [
        Resource(
            uri=f"{_SCHEME}://all",
            name="All Customers",
            description="Complete list of all customers.",
            mimeType="application/json",
        )
    ]


def get_templates() -> list[ResourceTemplate]:
    return [
        ResourceTemplate(
            uriTemplate=f"{_SCHEME}://{{id}}",
            name="Customer by ID",
            description="A single customer record looked up by ID.",
            mimeType="application/json",
        ),
        ResourceTemplate(
            uriTemplate=f"{_SCHEME}://{{id}}/orders",
            name="Customer Orders",
            description="All orders belonging to a customer.",
            mimeType="application/json",
        ),
    ]


def read(uri: str) -> str:
    """Return JSON string for the given customers:// URI."""
    if uri == f"{_SCHEME}://all":
        return json.dumps([c.to_dict() for c in store.customers.values()], indent=2)

    # customers://{id}/orders  — check before single-item so /orders suffix wins
    m = re.match(rf"^{_SCHEME}://([^/]+)/orders$", uri)
    if m:
        cid = m.group(1)
        if cid not in store.customers:
            return json.dumps({"error": "Not found"})
        result = [
            o.to_dict() for o in store.orders.values() if o.customer_id == cid
        ]
        return json.dumps(result, indent=2)

    # customers://{id}
    m = re.match(rf"^{_SCHEME}://([^/]+)$", uri)
    if m:
        cid = m.group(1)
        customer = store.customers.get(cid)
        if not customer:
            return json.dumps({"error": "Not found"})
        return json.dumps(customer.to_dict(), indent=2)

    return json.dumps({"error": f"Unknown resource URI: {uri}"})
