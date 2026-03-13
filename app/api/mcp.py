"""
MCP SDK tool and resource dispatcher.

Registers handlers for tools and resources on the shared Server instance.

Tools are organised by entity (customers, products, orders). Each entity module
exposes TOOL_DEFINITIONS (list[dict]) and handle(name, params) -> dict.

Resources are read-only and organised similarly, with get_resources(),
get_templates(), and read(uri) functions per entity module.

Logging uses two channels:
- Python stdlib logging (server-side, visible in server logs)
- send_log_message (MCP protocol, forwarded to the connected MCP client)
"""

from __future__ import annotations

import logging
import time
from typing import Any

from mcp.types import CallToolResult, Resource, ResourceTemplate, TextContent, Tool

from app.core.server import server
from app.resources import customers as customers_res
from app.resources import orders as orders_res
from app.resources import products as products_res
from app.tools import customers as customers_tools
from app.tools import orders as orders_tools
from app.tools import products as products_tools

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool registry — built once at import time from entity modules
# ---------------------------------------------------------------------------

# Maps tool name -> (entity_module, definition_dict)
_TOOL_REGISTRY: dict[str, tuple] = {}
for _entity_mod in [customers_tools, products_tools, orders_tools]:
    for _defn in _entity_mod.TOOL_DEFINITIONS:
        _TOOL_REGISTRY[_defn["name"]] = (_entity_mod, _defn)

# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------


@server.list_tools()
async def list_tools() -> list[Tool]:
    """Return all registered tool definitions."""
    logger.debug("tools/list called (%d tools registered)", len(_TOOL_REGISTRY))
    return [Tool(**defn) for _, defn in _TOOL_REGISTRY.values()]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
    """Dispatch a tool call and log the outcome via the MCP protocol."""
    ctx = server.request_context
    session = ctx.session

    if name not in _TOOL_REGISTRY:
        msg = f"Unknown tool: {name}"
        logger.warning("tools/call unknown tool=%s", name)
        await session.send_log_message(
            level="warning",
            data={"tool": name, "status": "unknown_tool", "error": msg},
            logger="mcp.tools",
        )
        return CallToolResult(
            content=[TextContent(type="text", text=msg)],
            isError=True,
        )

    await session.send_log_message(
        level="debug",
        data={"tool": name, "arguments": arguments},
        logger="mcp.tools",
    )

    start = time.perf_counter()
    try:
        entity_mod, _ = _TOOL_REGISTRY[name]
        result = entity_mod.handle(name, arguments)
        duration_ms = round((time.perf_counter() - start) * 1000)

        is_error: bool = result.get("isError", False)
        content = [
            TextContent(type="text", text=item["text"])
            for item in result.get("content", [])
            if item.get("type") == "text"
        ]

        if is_error:
            logger.warning(
                "tools/call tool=%s duration=%dms status=tool_error", name, duration_ms
            )
            await session.send_log_message(
                level="warning",
                data={"tool": name, "status": "tool_error", "duration_ms": duration_ms},
                logger="mcp.tools",
            )
        else:
            logger.info("tools/call tool=%s duration=%dms status=ok", name, duration_ms)
            await session.send_log_message(
                level="info",
                data={"tool": name, "status": "ok", "duration_ms": duration_ms},
                logger="mcp.tools",
            )

        return CallToolResult(content=content, isError=is_error)

    except Exception as exc:
        duration_ms = round((time.perf_counter() - start) * 1000)
        logger.exception("tools/call tool=%s raised unexpected error", name)
        await session.send_log_message(
            level="error",
            data={
                "tool": name,
                "status": "error",
                "error": str(exc),
                "duration_ms": duration_ms,
            },
            logger="mcp.tools",
        )
        return CallToolResult(
            content=[TextContent(type="text", text=f"Internal error: {exc}")],
            isError=True,
        )


# ---------------------------------------------------------------------------
# Resource handlers
# ---------------------------------------------------------------------------


@server.list_resources()
async def list_resources() -> list[Resource]:
    """Return all concrete (non-template) resources."""
    return (
        customers_res.get_resources()
        + products_res.get_resources()
        + orders_res.get_resources()
    )


@server.list_resource_templates()
async def list_resource_templates() -> list[ResourceTemplate]:
    """Return all URI-template resources."""
    return (
        customers_res.get_templates()
        + products_res.get_templates()
        + orders_res.get_templates()
    )


@server.read_resource()
async def read_resource(uri) -> str:
    """Route a resource read to the appropriate entity handler."""
    uri_str = str(uri)
    if uri_str.startswith("customers://"):
        return customers_res.read(uri_str)
    if uri_str.startswith("products://"):
        return products_res.read(uri_str)
    if uri_str.startswith("orders://"):
        return orders_res.read(uri_str)
    raise ValueError(f"No resource handler for URI: {uri_str}")
