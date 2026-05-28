def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "engine": "mermaid",
        "engineVersion": "11.11.0",
    }
