import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from google import genai
from pydantic import BaseModel, Field


load_dotenv()

app = Flask(__name__)


class ActionItem(BaseModel):
    task: str = Field(description="A specific task agreed during the meeting.")
    assignee: str | None = Field(
        description="The responsible person, or null if not stated."
    )
    deadline: str | None = Field(
        description="The deadline, or null if not stated."
    )
    status: str = Field(description="The initial status, always Pending.")


class MeetingAnalysis(BaseModel):
    summary: str = Field(description="A concise summary of the meeting.")
    action_items: list[ActionItem]


def analyze_notes(notes):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing from .env")

    client = genai.Client(api_key=api_key)
    prompt = (
        "Analyze these meeting notes. Return a concise summary and only "
        "action items that were actually agreed. Do not invent people or "
        "deadlines; use null when they are not stated. Set every status "
        "to Pending.\\n\\n"
        f"Meeting notes:\\n{notes}"
    )

    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": MeetingAnalysis.model_json_schema(),
        },
    )

    result = MeetingAnalysis.model_validate_json(response.text)
    return result.model_dump()


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

    try:
        return jsonify(analyze_notes(notes))
    except RuntimeError as error:
        return jsonify({"error": str(error)}), 503
    except Exception:
        app.logger.exception("Gemini analysis failed")
        return (
            jsonify({"error": "AI analysis failed. Check the server log."}),
            502,
        )


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True)
