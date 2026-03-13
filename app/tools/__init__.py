"""
Tool auto-discovery for the MCP server.

Any .py file in this package that defines both TOOL_DEFINITION and handle()
is automatically registered as an MCP tool. No other files need to be updated.

Tool file contract:
    TOOL_DEFINITION: dict  — must have keys: name, description, inputSchema
    handle(params: dict) -> dict  — returns an MCP content dict
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from types import ModuleType


def discover_tools() -> dict[str, ModuleType]:
    """
    Scan this package for tool modules and return a mapping of tool name -> module.

    A module is treated as a tool if it exposes both TOOL_DEFINITION and handle.
    """
    tools: dict[str, ModuleType] = {}
    package_dir = str(Path(__file__).parent)

    for _, module_name, _ in pkgutil.iter_modules([package_dir]):
        module = importlib.import_module(f"app.tools.{module_name}")
        if hasattr(module, "TOOL_DEFINITION") and hasattr(module, "handle"):
            name = module.TOOL_DEFINITION["name"]
            tools[name] = module

    return tools
