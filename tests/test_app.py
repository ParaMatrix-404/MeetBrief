import app as app_module


def test_health_returns_ok():
    client = app_module.app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_analyze_returns_summary_and_action_items(monkeypatch):
    expected = {
        "summary": "The team agreed on two follow-up tasks.",
        "action_items": [
            {
                "task": "Prepare the presentation",
                "assignee": "Rahul",
                "deadline": "Friday",
                "status": "Pending",
            },
            {
                "task": "Contact the client",
                "assignee": "Priya",
                "deadline": "tomorrow",
                "status": "Pending",
            },
        ],
    }
    monkeypatch.setattr(
        app_module,
        "analyze_notes",
        lambda notes, media_part=None: expected,
    )
    client = app_module.app.test_client()

    response = client.post(
        "/api/analyze",
        json={"notes": "Rahul will prepare the presentation by Friday."},
    )

    assert response.status_code == 200
    assert response.get_json() == expected


def test_analyze_rejects_missing_notes():
    client = app_module.app.test_client()

    response = client.post("/api/analyze", json={"notes": " "})

    assert response.status_code == 400
    assert response.get_json() == {
        "error": "Provide notes or an audio/video file."
    }
