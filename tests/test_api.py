"""
Basic server smoke tests using the starlette TestClient.
"""


def test_post_to_unknown_path_returns_404():
    """POST to an unknown path should return 404."""
    from starlette.testclient import TestClient
    from app.main import app

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/unknown")
    assert response.status_code == 404
