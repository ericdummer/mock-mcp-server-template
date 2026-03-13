"""
Tests for the mock MCP server — Customers, Products, and Orders.

Uses an in-memory MCP transport (no HTTP) via the mcp_session fixture in conftest.py.

Covers:
- tools/list: all 18 entity tools present, each has required fields
- Customer CRUD: create, get, update, delete, validation
- Product CRUD: create, get, update, delete, validation
- Order CRUD: create, update_status, add/remove products, delete, validation
- Resource reads: list_resources, list_resource_templates, read_resource
- Auth check at the HTTP level (POST /mcp without key → 401)
"""

from __future__ import annotations

import json

import pytest

from mcp import ClientSession


# ---------------------------------------------------------------------------
# Authentication (HTTP-level, starlette TestClient)
# ---------------------------------------------------------------------------


def test_mcp_without_api_key_returns_401():
    """POST /mcp without the API key header should return HTTP 401."""
    from starlette.testclient import TestClient

    from app.main import app

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/mcp")
    assert response.status_code == 401
    assert "X-Api-Key" in response.text


# ---------------------------------------------------------------------------
# tools/list
# ---------------------------------------------------------------------------

_EXPECTED_TOOLS = {
    "create_customer", "update_customer", "delete_customer", "get_customer", "list_customers",
    "create_product", "update_product", "delete_product", "get_product", "list_products",
    "create_order", "update_order_status", "add_products_to_order",
    "remove_products_from_order", "delete_order", "get_order",
    "list_orders", "list_orders_by_customer",
}


@pytest.mark.anyio
async def test_tools_list_includes_all_entity_tools(mcp_session: ClientSession):
    result = await mcp_session.list_tools()
    names = {t.name for t in result.tools}
    assert _EXPECTED_TOOLS <= names


@pytest.mark.anyio
async def test_tools_list_each_tool_has_required_fields(mcp_session: ClientSession):
    result = await mcp_session.list_tools()
    for tool in result.tools:
        assert tool.name
        assert tool.description
        assert tool.inputSchema is not None


# ---------------------------------------------------------------------------
# Customer tools
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_list_customers_returns_seed_data(mcp_session: ClientSession):
    result = await mcp_session.call_tool("list_customers", {})
    assert not result.isError
    customers = json.loads(result.content[0].text)
    assert len(customers) >= 3
    ids = {c["id"] for c in customers}
    assert "cust-001" in ids


@pytest.mark.anyio
async def test_get_customer_returns_correct_record(mcp_session: ClientSession):
    result = await mcp_session.call_tool("get_customer", {"id": "cust-001"})
    assert not result.isError
    c = json.loads(result.content[0].text)
    assert c["id"] == "cust-001"
    assert c["name"] == "Alice Johnson"


@pytest.mark.anyio
async def test_get_customer_not_found(mcp_session: ClientSession):
    result = await mcp_session.call_tool("get_customer", {"id": "cust-9999"})
    assert result.isError
    assert "not found" in result.content[0].text.lower()


@pytest.mark.anyio
async def test_create_customer_success(mcp_session: ClientSession):
    result = await mcp_session.call_tool(
        "create_customer",
        {"name": "Dana Lee", "email": "dana@example.com", "phone": "555-2001"},
    )
    assert not result.isError
    c = json.loads(result.content[0].text)
    assert c["name"] == "Dana Lee"
    assert "id" in c


@pytest.mark.anyio
async def test_create_customer_invalid_email(mcp_session: ClientSession):
    result = await mcp_session.call_tool(
        "create_customer",
        {"name": "Bad Email", "email": "notanemail", "phone": "555-0000"},
    )
    assert result.isError
    assert "@" in result.content[0].text or "email" in result.content[0].text.lower()


@pytest.mark.anyio
async def test_create_customer_appears_in_list(mcp_session: ClientSession):
    await mcp_session.call_tool(
        "create_customer",
        {"name": "Unique Customer XYZ", "email": "unique@example.com", "phone": "555-9999"},
    )
    result = await mcp_session.call_tool("list_customers", {})
    names = [c["name"] for c in json.loads(result.content[0].text)]
    assert "Unique Customer XYZ" in names


@pytest.mark.anyio
async def test_update_customer_changes_fields(mcp_session: ClientSession):
    created = await mcp_session.call_tool(
        "create_customer",
        {"name": "Temp Customer", "email": "temp@example.com", "phone": "555-1111"},
    )
    cid = json.loads(created.content[0].text)["id"]
    updated = await mcp_session.call_tool(
        "update_customer", {"id": cid, "name": "Updated Name", "phone": "555-2222"}
    )
    assert not updated.isError
    c = json.loads(updated.content[0].text)
    assert c["name"] == "Updated Name"
    assert c["phone"] == "555-2222"


@pytest.mark.anyio
async def test_delete_customer_with_orders_fails(mcp_session: ClientSession):
    # cust-001 has seed orders; deletion must be rejected
    result = await mcp_session.call_tool("delete_customer", {"id": "cust-001"})
    assert result.isError
    assert "order" in result.content[0].text.lower()


@pytest.mark.anyio
async def test_delete_customer_without_orders_succeeds(mcp_session: ClientSession):
    created = await mcp_session.call_tool(
        "create_customer",
        {"name": "No Orders", "email": "noorders@example.com", "phone": "555-4444"},
    )
    cid = json.loads(created.content[0].text)["id"]
    result = await mcp_session.call_tool("delete_customer", {"id": cid})
    assert not result.isError
    check = await mcp_session.call_tool("get_customer", {"id": cid})
    assert check.isError


# ---------------------------------------------------------------------------
# Product tools
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_list_products_returns_seed_data(mcp_session: ClientSession):
    result = await mcp_session.call_tool("list_products", {})
    assert not result.isError
    products = json.loads(result.content[0].text)
    assert len(products) >= 5
    ids = {p["id"] for p in products}
    assert "prod-001" in ids


@pytest.mark.anyio
async def test_get_product_returns_correct_record(mcp_session: ClientSession):
    result = await mcp_session.call_tool("get_product", {"id": "prod-002"})
    assert not result.isError
    p = json.loads(result.content[0].text)
    assert p["id"] == "prod-002"
    assert p["name"] == "Wireless Mouse"


@pytest.mark.anyio
async def test_get_product_not_found(mcp_session: ClientSession):
    result = await mcp_session.call_tool("get_product", {"id": "prod-9999"})
    assert result.isError


@pytest.mark.anyio
async def test_create_product_success(mcp_session: ClientSession):
    result = await mcp_session.call_tool(
        "create_product",
        {"name": "Test Gadget", "description": "A test gadget.", "price": 9.99, "stock": 5},
    )
    assert not result.isError
    p = json.loads(result.content[0].text)
    assert p["name"] == "Test Gadget"
    assert p["price"] == 9.99


@pytest.mark.anyio
async def test_update_product_changes_price(mcp_session: ClientSession):
    created = await mcp_session.call_tool(
        "create_product",
        {"name": "Price Test", "description": ".", "price": 10.0, "stock": 1},
    )
    pid = json.loads(created.content[0].text)["id"]
    updated = await mcp_session.call_tool("update_product", {"id": pid, "price": 19.99})
    assert not updated.isError
    assert json.loads(updated.content[0].text)["price"] == 19.99


@pytest.mark.anyio
async def test_delete_product_referenced_in_order_fails(mcp_session: ClientSession):
    # prod-001 is in order-001; deletion must be rejected
    result = await mcp_session.call_tool("delete_product", {"id": "prod-001"})
    assert result.isError
    assert "order" in result.content[0].text.lower()


@pytest.mark.anyio
async def test_delete_product_not_in_order_succeeds(mcp_session: ClientSession):
    created = await mcp_session.call_tool(
        "create_product",
        {"name": "Deletable", "description": "Safe to delete.", "price": 1.0, "stock": 0},
    )
    pid = json.loads(created.content[0].text)["id"]
    result = await mcp_session.call_tool("delete_product", {"id": pid})
    assert not result.isError
    check = await mcp_session.call_tool("get_product", {"id": pid})
    assert check.isError


# ---------------------------------------------------------------------------
# Order tools
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_list_orders_returns_seed_data(mcp_session: ClientSession):
    result = await mcp_session.call_tool("list_orders", {})
    assert not result.isError
    orders = json.loads(result.content[0].text)
    assert len(orders) >= 4


@pytest.mark.anyio
async def test_get_order_returns_correct_record(mcp_session: ClientSession):
    result = await mcp_session.call_tool("get_order", {"id": "order-001"})
    assert not result.isError
    o = json.loads(result.content[0].text)
    assert o["id"] == "order-001"
    assert o["customer_id"] == "cust-001"


@pytest.mark.anyio
async def test_create_order_success(mcp_session: ClientSession):
    result = await mcp_session.call_tool(
        "create_order",
        {"customer_id": "cust-002", "product_ids": ["prod-002", "prod-003"]},
    )
    assert not result.isError
    o = json.loads(result.content[0].text)
    assert o["customer_id"] == "cust-002"
    assert o["status"] == "pending"
    assert abs(o["total"] - (29.99 + 49.99)) < 0.01


@pytest.mark.anyio
async def test_create_order_invalid_customer(mcp_session: ClientSession):
    result = await mcp_session.call_tool(
        "create_order",
        {"customer_id": "cust-9999", "product_ids": ["prod-001"]},
    )
    assert result.isError
    assert "not found" in result.content[0].text.lower()


@pytest.mark.anyio
async def test_create_order_invalid_product(mcp_session: ClientSession):
    result = await mcp_session.call_tool(
        "create_order",
        {"customer_id": "cust-001", "product_ids": ["prod-9999"]},
    )
    assert result.isError


@pytest.mark.anyio
async def test_update_order_status_valid(mcp_session: ClientSession):
    result = await mcp_session.call_tool(
        "update_order_status", {"id": "order-003", "status": "shipped"}
    )
    assert not result.isError
    assert json.loads(result.content[0].text)["status"] == "shipped"


@pytest.mark.anyio
async def test_update_order_status_invalid(mcp_session: ClientSession):
    result = await mcp_session.call_tool(
        "update_order_status", {"id": "order-003", "status": "in_transit"}
    )
    assert result.isError


@pytest.mark.anyio
async def test_add_products_to_order(mcp_session: ClientSession):
    # Create a fresh order then add a product to it
    created = await mcp_session.call_tool(
        "create_order",
        {"customer_id": "cust-003", "product_ids": ["prod-002"]},
    )
    oid = json.loads(created.content[0].text)["id"]
    result = await mcp_session.call_tool(
        "add_products_to_order", {"id": oid, "product_ids": ["prod-003"]}
    )
    assert not result.isError
    o = json.loads(result.content[0].text)
    assert "prod-003" in o["product_ids"]
    assert abs(o["total"] - (29.99 + 49.99)) < 0.01


@pytest.mark.anyio
async def test_remove_products_from_order(mcp_session: ClientSession):
    created = await mcp_session.call_tool(
        "create_order",
        {"customer_id": "cust-001", "product_ids": ["prod-002", "prod-003"]},
    )
    oid = json.loads(created.content[0].text)["id"]
    result = await mcp_session.call_tool(
        "remove_products_from_order", {"id": oid, "product_ids": ["prod-003"]}
    )
    assert not result.isError
    o = json.loads(result.content[0].text)
    assert "prod-003" not in o["product_ids"]
    assert abs(o["total"] - 29.99) < 0.01


@pytest.mark.anyio
async def test_list_orders_by_customer(mcp_session: ClientSession):
    result = await mcp_session.call_tool(
        "list_orders_by_customer", {"customer_id": "cust-001"}
    )
    assert not result.isError
    orders = json.loads(result.content[0].text)
    assert len(orders) >= 2
    for o in orders:
        assert o["customer_id"] == "cust-001"


@pytest.mark.anyio
async def test_delete_order_succeeds(mcp_session: ClientSession):
    created = await mcp_session.call_tool(
        "create_order",
        {"customer_id": "cust-002", "product_ids": ["prod-005"]},
    )
    oid = json.loads(created.content[0].text)["id"]
    result = await mcp_session.call_tool("delete_order", {"id": oid})
    assert not result.isError
    check = await mcp_session.call_tool("get_order", {"id": oid})
    assert check.isError


# ---------------------------------------------------------------------------
# Resource handlers
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_list_resources_returns_concrete_resources(mcp_session: ClientSession):
    result = await mcp_session.list_resources()
    uris = {str(r.uri) for r in result.resources}
    assert "customers://all" in uris
    assert "products://all" in uris
    assert "orders://all" in uris


@pytest.mark.anyio
async def test_list_resource_templates(mcp_session: ClientSession):
    result = await mcp_session.list_resource_templates()
    templates = {t.uriTemplate for t in result.resourceTemplates}
    assert "customers://{id}" in templates
    assert "customers://{id}/orders" in templates
    assert "products://{id}" in templates
    assert "orders://{id}" in templates
    assert "orders://{id}/products" in templates


@pytest.mark.anyio
async def test_read_resource_customers_all(mcp_session: ClientSession):
    result = await mcp_session.read_resource("customers://all")
    data = json.loads(result.contents[0].text)
    assert isinstance(data, list)
    assert len(data) >= 3


@pytest.mark.anyio
async def test_read_resource_single_customer(mcp_session: ClientSession):
    result = await mcp_session.read_resource("customers://cust-002")
    data = json.loads(result.contents[0].text)
    assert data["id"] == "cust-002"
    assert data["name"] == "Bob Smith"


@pytest.mark.anyio
async def test_read_resource_customer_not_found(mcp_session: ClientSession):
    result = await mcp_session.read_resource("customers://cust-9999")
    data = json.loads(result.contents[0].text)
    assert "error" in data


@pytest.mark.anyio
async def test_read_resource_customer_orders(mcp_session: ClientSession):
    result = await mcp_session.read_resource("customers://cust-001/orders")
    orders = json.loads(result.contents[0].text)
    assert isinstance(orders, list)
    assert len(orders) >= 2
    for o in orders:
        assert o["customer_id"] == "cust-001"


@pytest.mark.anyio
async def test_read_resource_products_all(mcp_session: ClientSession):
    result = await mcp_session.read_resource("products://all")
    data = json.loads(result.contents[0].text)
    assert len(data) >= 5


@pytest.mark.anyio
async def test_read_resource_single_product(mcp_session: ClientSession):
    result = await mcp_session.read_resource("products://prod-001")
    data = json.loads(result.contents[0].text)
    assert data["id"] == "prod-001"


@pytest.mark.anyio
async def test_read_resource_orders_all(mcp_session: ClientSession):
    result = await mcp_session.read_resource("orders://all")
    data = json.loads(result.contents[0].text)
    assert len(data) >= 4


@pytest.mark.anyio
async def test_read_resource_order_products(mcp_session: ClientSession):
    result = await mcp_session.read_resource("orders://order-001/products")
    products = json.loads(result.contents[0].text)
    assert isinstance(products, list)
    assert len(products) >= 1
    assert all("price" in p for p in products)


