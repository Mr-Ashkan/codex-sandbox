from __future__ import annotations

import json
import os
import random
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from urllib.parse import parse_qs, urlparse

from jinja2 import Environment, FileSystemLoader
from PIL import Image, ImageDraw

TEMPLATE_ENV = Environment(loader=FileSystemLoader("app/templates"))
STATIC_DIR = os.path.join("app", "static")


class Handler(BaseHTTPRequestHandler):
    """HTTP handler serving application endpoints."""

    def do_GET(self) -> None:  # noqa: D401
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._json_response({"ok": True})
        elif parsed.path == "/openapi.json":
            self._json_response({"openapi": "3.0.0"})
        elif parsed.path == "/":
            template = TEMPLATE_ENV.get_template("index.html")
            content = template.render()
            self._html_response(content)
        elif parsed.path.startswith("/static/"):
            self._serve_static(parsed.path[len("/static/") :])
        elif parsed.path == "/api/generate":
            self._generate_image(parsed.query)
        else:
            self.send_response(404)
            self.end_headers()

    # Helpers -----------------------------------------------------------------
    def _json_response(self, data: dict) -> None:
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html_response(self, content: str) -> None:
        body = content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self, path: str) -> None:
        full_path = os.path.join(STATIC_DIR, path)
        if os.path.isfile(full_path):
            with open(full_path, "rb") as file:
                content = file.read()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()

    def _generate_image(self, query: str) -> None:
        params = parse_qs(query)
        width = int(params.get("w", ["1280"])[0])
        height = int(params.get("h", ["720"])[0])
        palette = [f"#{c}" for c in params.get("palette", ["000000"])[0].split(",")]
        seed = int(params.get("seed", ["0"])[0])
        random.seed(seed)

        image = Image.new("RGB", (width, height), palette[0])
        draw = ImageDraw.Draw(image)
        stripe_width = max(1, width // len(palette))
        for i, color in enumerate(palette):
            x0 = i * stripe_width
            x1 = width if i == len(palette) - 1 else (i + 1) * stripe_width
            draw.rectangle([x0, 0, x1, height], fill=color)

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        body = buffer.getvalue()

        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def create_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    """Create a configured HTTP server."""
    return ThreadingHTTPServer((host, port), Handler)
