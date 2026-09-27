# MeetBrief

MeetBrief turns meeting notes or recordings into a concise summary and a structured list of action items. It is built with Flask, uses the Google Gemini API for analysis, and can be packaged with Docker and deployed to Render through a Jenkins pipeline.

## Features

- Analyze pasted meeting notes.
- Analyze audio files: `.mp3`, `.wav`, and `.m4a`.
- Analyze video files: `.mp4`, `.mov`, and `.webm`.
- Return a meeting summary and action items with task, assignee, deadline, and initial status.
- Provide a web interface, JSON API, and health-check endpoint.
- Run tests and lint checks in Jenkins, build a Docker image, and trigger a Render deployment.

Uploaded media is limited to 20 MB. The application does not currently use a database; results and UI edits are not saved as meeting history.

## Technology

- Python 3.14 and Flask
- Google Gemini API (`google-genai`)
- Pydantic for the analysis response structure
- pytest and flake8
- Docker and Jenkins
- Render

## Project structure

```text
MeetBrief/
├── app.py                  # Flask app, API routes, validation, Gemini integration
├── templates/
│   └── index.html          # MeetBrief web interface
├── tests/
│   └── test_app.py         # Automated Flask API tests
├── requirements.txt        # Runtime dependencies
├── requirements-dev.txt    # Test and lint dependencies
├── Dockerfile              # Instructions to build the app image
├── Jenkinsfile             # Test, image build, and Render deploy stages
└── jenkins/                # Local Jenkins Docker setup
```

## Run locally on Windows

Open PowerShell in the project folder and create a virtual environment:

```powershell
py -3.14 -m venv .venv
```

Install the packages without activating the environment (this also works when PowerShell script activation is restricted):

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Create a `.env` file in the project root with your own Gemini API key:

```text
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3.5-flash-lite
```

Keep `.env` private and never commit it. Start Flask:

```powershell
.venv\Scripts\python.exe app.py
```

Visit <http://127.0.0.1:5000/>. Stop the local server with `Ctrl+C`.

## API endpoints

### `GET /`

Serves the web interface.

### `POST /api/analyze`

Accepts JSON meeting notes:

```json
{
  "notes": "Rahul will prepare the presentation by Friday."
}
```

It can also accept `multipart/form-data` with an optional `notes` field and a media upload in the `file` field. The response is JSON in this shape:

```json
{
  "summary": "The team agreed that Rahul will prepare the presentation by Friday.",
  "action_items": [
    {
      "task": "Prepare the presentation",
      "assignee": "Rahul",
      "deadline": "Friday",
      "status": "Pending"
    }
  ]
}
```

The model is instructed not to invent assignments or deadlines. If they are not stated, the corresponding values should be `null`.

### `GET /health`

Returns `{"status":"ok"}` when the Flask service is responding.

Common error responses include `400` for invalid or missing input, `413` for an upload over 20 MB, `415` for an unsupported request content type, `502` when AI analysis fails, and `503` when the Gemini API key is missing.

## Run tests and lint

```powershell
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m flake8 app.py tests
```

## Docker

Build the image from the project root:

```powershell
docker build -t meetbrief .
```

Run it locally, passing the API key as an environment variable:

```powershell
docker run --rm -p 5000:5000 -e GEMINI_API_KEY=your-gemini-api-key meetbrief
```

Then visit <http://localhost:5000/>. Do not put the real API key in this README or in the Docker image.

## Jenkins and deployment

The root `Jenkinsfile` defines these stages in order:

1. **Test and lint** — installs development requirements in a Python Docker container, runs pytest, and runs flake8.
2. **Build MeetBrief image** — builds a Docker image tagged with the Jenkins build number.
3. **Deploy to Render** — reads the `render-deploy-hook` secret from Jenkins Credentials and sends a POST request to trigger a Render deployment.

If an earlier stage fails, Jenkins marks the pipeline as failed and does not proceed to the later stages. The current Jenkins job has been run manually with **Build Now**; automatic builds on every push require a configured webhook or Jenkins trigger.

Set `GEMINI_API_KEY` in Render's environment settings. Keep the Render deploy hook in Jenkins Credentials with the ID `render-deploy-hook`. Do not commit secret values.

## Live links

- Application: <https://meetbrief-uf1c.onrender.com/>
- Health check: <https://meetbrief-uf1c.onrender.com/health>
- GitHub repository: <https://github.com/ParaMatrix-404/MeetBrief>

## Limitations

- There is no database or persistent meeting history yet.
- The application depends on access to the Gemini API and a valid API key.
- Render free services can take time to wake after being idle.
- The current Jenkins setup is intended for local demonstration; Jenkins is not exposed as a public service.
