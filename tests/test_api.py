"""
Basic server smoke tests.
"""


def test_post_to_unknown_path_returns_404(client):
    """POST to an unknown path should return 404."""
    response = client.post("/unknown")
    assert response.status_code == 404
