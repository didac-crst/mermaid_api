def test_validate_valid_mermaid(client):
    response = client.post("/validate", json={"code": "flowchart TD\nA-->B"})

    assert response.status_code == 200
    assert response.json() == {"valid": True, "diagramType": "flowchart-v2"}


def test_validate_invalid_mermaid(client):
    response = client.post("/validate", json={"code": "invalid diagram"})

    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "error": {
                "code": "MERMAID_PARSE_ERROR",
                "message": "Unexpected token",
            }
        }
    }
