def test_validate_valid_mermaid(client):
    response = client.post("/validate", json={"code": "flowchart TD\nA-->B"})

    assert response.status_code == 200
    assert response.json() == {"valid": True, "diagramType": "flowchart-v2"}


def test_validate_invalid_mermaid(client):
    response = client.post("/validate", json={"code": "invalid diagram"})

    assert response.status_code == 400
    assert response.json() == {
        "valid": False,
        "error": {
            "code": "MERMAID_PARSE_ERROR",
            "message": "Unexpected token",
        },
    }


def test_validate_invalid_mermaid_with_input_preview(client):
    response = client.post(
        "/validate",
        json={"code": "invalid diagram"},
        headers={"X-Include-Input": "true"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "valid": False,
        "error": {
            "code": "MERMAID_PARSE_ERROR",
            "message": "Unexpected token",
        },
        "originalSyntaxPreview": "invalid diagram",
        "originalSyntaxTruncated": False,
    }


def test_validate_input_preview_is_truncated(client):
    long_code = "invalid " + ("A" * 3000)
    response = client.post(
        "/validate",
        json={"code": long_code},
        headers={"X-Include-Input": "true"},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["valid"] is False
    assert body["error"]["code"] == "MERMAID_PARSE_ERROR"
    assert body["originalSyntaxPreview"] == long_code[:2048]
    assert body["originalSyntaxTruncated"] is True
