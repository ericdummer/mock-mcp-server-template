"""MCP SDK Server singleton.

Import this module to access the shared Server instance used across
the dispatcher and the ASGI application.
"""

from mcp.server import Server

server = Server("mock-mcp-server")
