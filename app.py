from flask import Flask, jsonify, request

app = Flask(__name__)


def analyze_notes(notes):
    sentences = [part.strip() for part in notes.split(".") if part.strip()]

    action_items = []
    keywords = ("will ", " must ", " should ", " needs to ", " need to ")

    for sentence in sentences:
        lowered = sentence.lower()
        if any(keyword in f" {lowered} " for keyword in keywords):
            action_items.append({
                "task": sentence,
                "assignee": None,
                "deadline": None,
                "status": "Pending",
            })

    return {
        "summary": " ".join(sentences[:2]),
        "action_items": action_items,
    }


@app.get("/")
def home():
    return (
        "<h1>MeetBrief</h1>"
        "<p>Meeting summary and action-item service</p>"
    )


@app.post("/api/analyze")
def analyze():
    data = request.get_json(silent=True) or {}
    notes = data.get("notes", "")

    if not isinstance(notes, str) or not notes.strip():
        return jsonify({"error": "Please provide meeting notes."}), 400

    return jsonify(analyze_notes(notes))


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True)