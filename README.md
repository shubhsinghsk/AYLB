# AYLB Logistics

AYLB Logistics is a FastAPI web application that serves the existing Jinja templates and static assets.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

The app is available at <http://localhost:8000>. For development, FastAPI's interactive API documentation is at <http://localhost:8000/docs>.

The SQLite database is stored at `instance/site.db`. Contact form submissions are appended to `contacts.csv`. Configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `EMAIL_FROM`, and `EMAIL_TO` to send contact emails.
