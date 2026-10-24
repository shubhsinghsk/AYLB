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

The SQLite database is stored at `instance/site.db`. Contact form submissions are appended to `contacts.csv`. For Render's Free plan, configure `GMAIL_API_CLIENT_ID`, `GMAIL_API_CLIENT_SECRET`, and `GMAIL_API_REFRESH_TOKEN` to send Contact and Careers notifications through Gmail's HTTPS API. The local helper `scripts/get_gmail_refresh_token.py` prints these values after Google OAuth authorization. If Gmail API settings are absent, the app can use the optional SMTP settings in `env.example` on hosts that permit SMTP. Never commit `.env`, OAuth credentials, refresh tokens, or service-account keys.

## Careers and Google Sheets

The Careers page reads roles from the `OpenPositions` tab and appends applications to the `Applications` tab in the configured spreadsheet. Create these first-row headers:

- `OpenPositions`: `title`, `location`, `employment_type`, `description`, `department`, `active`
- `Applications`: `timestamp_utc`, `applicant_name`, `applicant_email`, `applicant_phone`, `desired_role`, `cover_letter`, `resume_filename`, `status`

Set `GOOGLE_SHEETS_SPREADSHEET_ID` to the ID in the spreadsheet URL and set `GOOGLE_JOBS_RANGE` / `GOOGLE_APPLICATIONS_RANGE` if the tab names or ranges differ. Create a Google service account with the Sheets API enabled, then share the spreadsheet with the service account's `client_email` as an Editor. On deployment, set `GOOGLE_SHEETS_CREDENTIALS_JSON` to the service-account JSON as a single environment variable, or use `GOOGLE_SHEETS_CREDENTIALS_FILE` to point to a securely mounted file. Never commit service-account credentials. Mark a role's `active` cell `TRUE` to publish it; set it to `FALSE` to hide it. The application form checks that the selected role is still active before recording a submission. Resume files are limited to PDF or DOCX and 5 MB; they are attached to the recruiting email and not stored in the spreadsheet.
