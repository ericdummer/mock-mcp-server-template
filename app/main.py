"""Mock MCP server entry point.

Starts a plain HTTP server exposing the JSON-RPC 2.0 MCP endpoint at POST /mcp.
"""

from __future__ import annotations

import logging
from http.server import BaseHTTPRequestHandler, HTTPServer

from app.api.mcp import handle_mcp_request
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class MCPRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the MCP server."""

    def do_POST(self) -> None:
        if self.path == "/mcp":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else b""
            api_key = self.headers.get("X-Goog-Api-Key")
            response = handle_mcp_request(body, api_key)
            response_bytes = response.model_dump_json().encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response_bytes)))
            self.end_headers()
            self.wfile.write(response_bytes)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        logger.debug(format, *args)


def create_server(host: str = "0.0.0.0", port: int = 8000) -> HTTPServer:
    """Create and return the HTTP server (does not start it)."""
    return HTTPServer((host, port), MCPRequestHandler)


if __name__ == "__main__":
    import logging as _logging

    _logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    settings = get_settings()
    server = create_server(settings.host, settings.port)
    logger.info("MCP server listening on http://%s:%s/mcp", settings.host, settings.port)
    server.serve_forever()
