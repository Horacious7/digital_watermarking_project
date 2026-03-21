from io import BytesIO

import numpy as np
import pytest

import api as api_module


@pytest.fixture
def client():
    """Flask test client fixture."""
    api_module.app.config["TESTING"] = True
    with api_module.app.test_client() as test_client:
        yield test_client


@pytest.fixture
def png_file_bytes():
    """
    Small in-memory pseudo image payload for multipart tests.
    Content is not parsed when heavy ops are mocked.
    """
    return b"\x89PNG\r\n\x1a\nfakepngdata"


def _multipart_image(filename="test.png", payload=b"dummy"):
    return {"image": (BytesIO(payload), filename)}


def test_health_endpoint_ok(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "ok"


def test_capacity_missing_file_returns_400(client):
    resp = client.post("/api/capacity", data={}, content_type="multipart/form-data")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_capacity_invalid_extension_returns_400(client, png_file_bytes):
    data = _multipart_image(filename="bad.txt", payload=png_file_bytes)
    resp = client.post("/api/capacity", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_embed_missing_file_returns_400(client):
    resp = client.post("/api/embed", data={}, content_type="multipart/form-data")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_embed_missing_message_returns_400(client, png_file_bytes):
    data = _multipart_image(payload=png_file_bytes)
    resp = client.post("/api/embed", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_embed_missing_private_key_returns_400(client, png_file_bytes, monkeypatch):
    """Bypass heavy image ops and capacity to assert input validation flow."""
    monkeypatch.setattr(api_module.cv2, "imread", lambda *args, **kwargs: np.zeros((64, 64, 3), dtype=np.uint8))
    monkeypatch.setattr(api_module.pywt, "dwt2", lambda *args, **kwargs: (np.zeros((32, 32), dtype=np.float32), None))
    monkeypatch.setattr(api_module, "bytes_to_bits", lambda b: "0" * 64)

    data = {
        "image": (BytesIO(png_file_bytes), "ok.png"),
        "message": "hello",
        "block_size": "8",
    }
    resp = client.post("/api/embed", data=data, content_type="multipart/form-data")
    assert resp.status_code == 400
    assert "Private key is required" in resp.get_json()["error"]


def test_verify_missing_file_returns_400(client):
    resp = client.post("/api/verify", data={}, content_type="multipart/form-data")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_verify_missing_public_key_returns_400(client, png_file_bytes, monkeypatch):
    """Mock extraction/parsing path so we can validate key requirement behavior."""
    monkeypatch.setattr(api_module, "detect_block_size", lambda *args, **kwargs: 8)
    monkeypatch.setattr(api_module.cv2, "imread", lambda *args, **kwargs: np.zeros((64, 64, 3), dtype=np.uint8))
    monkeypatch.setattr(api_module.pywt, "dwt2", lambda *args, **kwargs: (np.zeros((32, 32), dtype=np.float32), None))

    # Build extracted payload: [sig_len=1][sig=0x01]["m"][terminator]
    payload = b"\x00\x00\x00\x01" + b"\x01" + b"m" + b"\x00\x00\x00\x00"
    bit_payload = "".join(f"{byte:08b}" for byte in payload)
    monkeypatch.setattr(api_module, "extract_watermark", lambda *args, **kwargs: "00000000" + bit_payload)

    data = _multipart_image(payload=png_file_bytes)
    resp = client.post("/api/verify", data=data, content_type="multipart/form-data")

    assert resp.status_code == 400
    assert "Public key is required" in resp.get_json()["error"]
