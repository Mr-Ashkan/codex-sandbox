import json
import os
import sys
import threading

sys.path.insert(0, os.getcwd())
from http.client import HTTPConnection

from app.main import create_server

PORT = 8001


def _run_server():
    server = create_server(port=PORT)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    return server, thread


SERVER, THREAD = _run_server()


def teardown_module(_: object) -> None:
    SERVER.shutdown()
    THREAD.join()


def _request(path: str):
    conn = HTTPConnection("127.0.0.1", PORT)
    conn.request("GET", path)
    response = conn.getresponse()
    data = response.read()
    conn.close()
    return response, data


def test_health():
    response, data = _request("/health")
    assert response.status == 200
    assert json.loads(data) == {"ok": True}


def test_openapi():
    response, _ = _request("/openapi.json")
    assert response.status == 200


def test_index_template():
    response, data = _request("/")
    assert response.status == 200
    assert b"Hello, world!" in data


def test_static_file_served():
    response, data = _request("/static/test.txt")
    assert response.status == 200
    assert data.strip() == b"static file"


def test_generate_png():
    path = (
        "/api/generate?style=sinewaves&w=1280&h=720&"
        "palette=ff6b6b,ffd93d,6a93ff&seed=1"
    )
    response, _ = _request(path)
    assert response.status == 200
    assert response.getheader("Content-Type") == "image/png"
