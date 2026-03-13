"""
Order resources — read-only MCP resource handlers.

Concrete resources:
  orders://all              — all orders as JSON array

Resource templates:
  orders://{id}             — single order by ID
  orders://{id}/products    — full product objects for all product_ids in an order
"""

from __future__ import annotations

import json
import re

from mcp.types import Resource, ResourceTemplate

import app.data.store as store

_SCHEME = "orders"


def get_resources() -> list[Resource]:
    return [
        Resource(
            uri=f"{_SCHEME}://all",
            name="All Orders",
            description="Complete list of all orders.",
            mimeType="application/json",
        )
    ]


def get_templates() -> list[ResourceTemplate]:
    return [
        ResourceTemplate(
            uriTemplate=f"{_SCHEME}://{{id}}",
            name="Order by ID",
            description="A single order record looked up by ID.",
            mimeType="application/json",
        ),
        ResourceTemplate(
            uriTemplate=f"{_SCHEME}://{{id}}/products",
            name="Order Products",
            description="Full product objects for every product ID in an order.",
            mimeType="application/json",
        ),
    ]


def read(uri: str) -> str:
    """Return JSON string for the given orders:// URI."""
    if uri == f"{_SCHEME}://all":
        return json.dumps([o.to_dict() for o in store.orders.values()], indent=2)

    # orders://{id}/products — check before single-item so /products suffix wins
    m = re.match(rf"^{_SCHEME}://([^/]+)/products$", uri)
    if m:
        oid = m.group(1)
        order = store.orders.get(oid)
        if not order:
            return json.dumps({"error": "Not found"})
        products = [
            store.products[pid].to_dict()
            for pid in order.product_ids
            if pid in store.products
        ]
        return json.dumps(products, indent=2)

    # orders://{id}
    m = re.match(rf"^{_SCHEME}://([^/]+)$", uri)
    if m:
        oid = m.group(1)
        order = store.orders.get(oid)
        if not order:
            return json.dumps({"error": "Not found"})
        return json.dumps(order.to_dict(), indent=2)

    return json.dumps({"error": f"Unknown resource URI: {uri}"})
