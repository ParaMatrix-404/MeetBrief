
from app import app


def test_health_returns_ok():
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_analyze_returns_summary_and_action_items():
    client = app.test_client()

    response = client.post(
        "/api/analyze",
        json={
            "notes": (
                "Rahul will prepare the presentation by Friday. "
                "Priya needs to contact the client tomorrow."
            )
        },
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["summary"]
    assert len(data["action_items"]) == 2
    assert data["action_items"][0]["status"] == "Pending"


def test_analyze_rejects_missing_notes():
    client = app.test_client()

    response = client.post("/api/analyze", json={"notes": " "})

    assert response.status_code == 400
    assert response.get_json() == {"error": "Please provide meeting notes."}
