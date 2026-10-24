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

The SQLite database is stored at `instance/site.db`. Contact form submissions are appended to `contacts.csv`. Copy `env.example` to `.env` and set the SMTP values to enable Contact and Careers email notifications. Use `SMTP_SECURITY=starttls` with port 587, or `SMTP_SECURITY=ssl` with port 465. `auto` selects SSL for 465 and STARTTLS for other ports. The sending account may also require an app password or provider-specific SMTP credentials.

## Careers and Google Sheets

The Careers page reads roles from the `OpenPositions` tab and appends applications to the `Applications` tab in the configured spreadsheet. Create these first-row headers:

- `OpenPositions`: `title`, `location`, `employment_type`, `description`, `department`, `active`
- `Applications`: `timestamp_utc`, `applicant_name`, `applicant_email`, `applicant_phone`, `desired_role`, `cover_letter`, `resume_filename`, `status`

Set `GOOGLE_SHEETS_SPREADSHEET_ID` to the ID in the spreadsheet URL and set `GOOGLE_JOBS_RANGE` / `GOOGLE_APPLICATIONS_RANGE` if the tab names or ranges differ. Create a Google service account with the Sheets API enabled, then share the spreadsheet with the service account's `client_email` as an Editor. On deployment, set `GOOGLE_SHEETS_CREDENTIALS_JSON` to the service-account JSON as a single environment variable, or use `GOOGLE_SHEETS_CREDENTIALS_FILE` to point to a securely mounted file. Never commit service-account credentials. Mark a role's `active` cell `TRUE` to publish it; set it to `FALSE` to hide it. The application form checks that the selected role is still active before recording a submission. Resume files are limited to PDF or DOCX and 5 MB; they are attached to the recruiting email and not stored in the spreadsheet.
