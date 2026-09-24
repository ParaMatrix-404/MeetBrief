import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

MEDIA_MIME_TYPES = {
    ".mp3": "audio/mp3",
    ".wav": "audio/wav",
    ".m4a": "audio/m4a",
    ".mp4": "video/mp4",
    ".mov": "video/mov",
    ".webm": "video/webm",
}


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


def generate_analysis(prompt, media_part=None):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing from .env")

    client = genai.Client(api_key=api_key)
    contents = [prompt]

    if media_part is not None:
        contents.append(media_part)

    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        contents=contents,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": MeetingAnalysis.model_json_schema(),
        },
    )

    result = MeetingAnalysis.model_validate_json(response.text)
    return result.model_dump()


def analyze_notes(notes, media_part=None):
    source = notes.strip()

    if media_part is not None and not source:
        source = "Use the attached audio or video as the meeting source."

    prompt = (
        "Analyze the meeting source. Return a concise summary and only "
        "action items that were actually agreed. Do not invent people or "
        "deadlines; use null when they are not stated. Set every status "
        "to Pending.\n\n"
        f"Meeting source:\n{source}"
    )

    return generate_analysis(prompt, media_part)


@app.get("/")
def home():
    return (
        "<h1>MeetBrief</h1>"
        "<p>Meeting summary and action-item service</p>"
    )


@app.post("/api/analyze")
def analyze():
    media_part = None

    if request.is_json:
        data = request.get_json(silent=True) or {}
        notes = data.get("notes", "")
    elif request.mimetype == "multipart/form-data":
        notes = request.form.get("notes", "")
        upload = request.files.get("file")

        if upload and upload.filename:
            extension = Path(upload.filename).suffix.lower()
            mime_type = MEDIA_MIME_TYPES.get(extension)

            if mime_type is None:
                return (
                    jsonify({"error": "Unsupported audio or video format."}),
                    400,
                )

            file_bytes = upload.read()
            if not file_bytes:
                return jsonify({"error": "The uploaded file is empty."}), 400

            media_part = types.Part.from_bytes(
                data=file_bytes,
                mime_type=mime_type,
            )
    else:
        return jsonify({"error": "Use JSON or multipart form data."}), 415

    if not isinstance(notes, str):
        return jsonify({"error": "Meeting notes must be text."}), 400

    if not notes.strip() and media_part is None:
        return jsonify({"error": "Provide notes or an audio/video file."}), 400

    try:
        return jsonify(analyze_notes(notes, media_part))
    except RuntimeError as error:
        return jsonify({"error": str(error)}), 503
    except Exception:
        app.logger.exception("Gemini analysis failed")
        return (
            jsonify({"error": "AI analysis failed. Check the server log."}),
            502,
        )


@app.errorhandler(413)
def request_too_large(error):
    return jsonify({"error": "The upload must be 10 MB or smaller."}), 413


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True)
