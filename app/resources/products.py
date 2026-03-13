"""
Product resources — read-only MCP resource handlers.

Concrete resources:
  products://all     — all products as JSON array

Resource templates:
  products://{id}    — single product by ID
"""

from __future__ import annotations

import json
import re

from mcp.types import Resource, ResourceTemplate

import app.data.store as store

_SCHEME = "products"


def get_resources() -> list[Resource]:
    return [
        Resource(
            uri=f"{_SCHEME}://all",
            name="All Products",
            description="Complete list of all products.",
            mimeType="application/json",
        )
    ]


def get_templates() -> list[ResourceTemplate]:
    return [
        ResourceTemplate(
            uriTemplate=f"{_SCHEME}://{{id}}",
            name="Product by ID",
            description="A single product record looked up by ID.",
            mimeType="application/json",
        ),
    ]


def read(uri: str) -> str:
    """Return JSON string for the given products:// URI."""
    if uri == f"{_SCHEME}://all":
        return json.dumps([p.to_dict() for p in store.products.values()], indent=2)

    m = re.match(rf"^{_SCHEME}://([^/]+)$", uri)
    if m:
        pid = m.group(1)
        product = store.products.get(pid)
        if not product:
            return json.dumps({"error": "Not found"})
        return json.dumps(product.to_dict(), indent=2)

    return json.dumps({"error": f"Unknown resource URI: {uri}"})
