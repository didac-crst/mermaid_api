def test_render_svg(client):
    response = client.post(
        "/render",
        json={"code": "flowchart TD\nA-->B", "format": "svg", "transparent": True},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert response.headers["cache-control"] == "no-store"
    assert response.content.startswith(b"<svg")


def test_render_png(client):
    response = client.post("/render", json={"code": "flowchart TD\nA-->B", "format": "png"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")


def test_render_jpeg(client):
    response = client.post("/render", json={"code": "flowchart TD\nA-->B", "format": "jpg"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.content.startswith(b"\xff\xd8")


def test_render_parse_error(client):
    response = client.post("/render", json={"code": "invalid", "format": "png"})

    assert response.status_code == 400
    assert response.json()["detail"]["error"]["code"] == "MERMAID_PARSE_ERROR"


def test_render_timeout(client):
    response = client.post("/render", json={"code": "timeout", "format": "png"})

    assert response.status_code == 504
    assert response.json()["detail"]["error"]["code"] == "MERMAID_RENDER_TIMEOUT"


def test_render_invalid_option(client):
    response = client.post("/render", json={"code": "flowchart TD\nA-->B", "scale": 9})

    assert response.status_code == 422
