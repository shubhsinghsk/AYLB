"""Website routes implemented with FastAPI and Starlette sessions."""

import csv
import asyncio
import base64
import html
import json
import logging
import os
import smtplib
import ssl
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

from fastapi import Request
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from starlette.datastructures import UploadFile
from werkzeug.security import check_password_hash, generate_password_hash

from AYLB_LOGIS import PACKAGE_DIR, PROJECT_DIR, SessionLocal, app
from AYLB_LOGIS.config import SERVICES
from AYLB_LOGIS.form import LoginForm, RegistrationForm
from AYLB_LOGIS.models import User

templates = Jinja2Templates(directory=PACKAGE_DIR / "templates")
logger = logging.getLogger(__name__)
CONTACTS_CSV = PROJECT_DIR / "contacts.csv"
if not CONTACTS_CSV.exists():
    with CONTACTS_CSV.open("w", newline="", encoding="utf-8") as file:
        csv.writer(file).writerow(["timestamp", "name", "company", "email", "phone", "city", "service", "message"])


def flash(request: Request, message: str, category: str = "message"):
    request.session.setdefault("_flashes", []).append((category, message))


def get_flashed_messages(request: Request, with_categories=False):
    messages = request.session.pop("_flashes", [])
    return messages if with_categories else [message for _, message in messages]


def render(request: Request, template: str, **context):
    with SessionLocal() as db:
        user_id = request.session.get("user_id")
        current_user = db.get(User, user_id) if user_id else None
    def template_url_for(name, **params):
        # Flask templates use ``filename`` for static files; Starlette's mount
        # route calls that parameter ``path``.
        if name == "static" and "filename" in params:
            params["path"] = params.pop("filename")
        return request.url_for(name, **params)

    return templates.TemplateResponse(
        request=request,
        name=template,
        context={
            "current_user": current_user,
            "url_for": template_url_for,
            "get_flashed_messages": lambda with_categories=False: get_flashed_messages(request, with_categories),
            **context,
        },
    )


def redirect(name: str, request: Request, status_code=303, **params):
    return RedirectResponse(str(request.url_for(name, **params)), status_code=status_code)


def smtp_ssl_context():
    """Use a known CA bundle when the Python installation has no system roots."""
    custom_bundle = os.getenv("SMTP_CA_BUNDLE", "").strip()
    if custom_bundle:
        return ssl.create_default_context(cafile=custom_bundle)
    try:
        import certifi
    except ImportError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())


def send_email(subject, html_content, plain_text=None, attachment=None, reply_to=None):
    # Gmail's HTTPS API works on Render's Free plan, where outbound SMTP is blocked.
    if os.getenv("GMAIL_API_REFRESH_TOKEN", "").strip():
        return send_email_with_gmail_api(
            subject, html_content, plain_text, attachment, reply_to
        )

    host = os.getenv("SMTP_HOST")
    try:
        port = int(os.getenv("SMTP_PORT", "587"))
    except ValueError:
        logger.error("SMTP_PORT must be a valid port number")
        return False, "SMTP_PORT must be a valid port number."
    user, password = os.getenv("SMTP_USERNAME"), os.getenv("SMTP_PASSWORD")
    sender, recipient = os.getenv("EMAIL_FROM"), os.getenv("EMAIL_TO")
    if not all([host, user, password, sender, recipient]):
        logger.error("SMTP delivery is not configured: one or more required settings are missing")
        return False, "SMTP not configured properly."
    message = EmailMessage()
    message["Subject"], message["From"], message["To"] = subject, sender, recipient
    if reply_to:
        message["Reply-To"] = reply_to
    if plain_text:
        message.set_content(plain_text)
        message.add_alternative(html_content, subtype="html")
    else:
        message.set_content(html_content, subtype="html")
    if attachment:
        filename, content, content_type = attachment
        maintype, subtype = content_type.split("/", 1)
        message.add_attachment(content, maintype=maintype, subtype=subtype, filename=filename)
    try:
        security = os.getenv("SMTP_SECURITY", "auto").strip().lower()
        use_ssl = security == "ssl" or (security == "auto" and port == 465)
        use_starttls = security == "starttls" or (security == "auto" and port != 465)
        if security not in {"auto", "ssl", "starttls", "none"}:
            return False, "SMTP_SECURITY must be auto, ssl, starttls, or none."
        tls_context = smtp_ssl_context() if use_ssl or use_starttls else None
        if use_ssl:
            server_context = smtplib.SMTP_SSL(host, port, timeout=15, context=tls_context)
        else:
            server_context = smtplib.SMTP(host, port, timeout=15)
        with server_context as server:
            if use_starttls:
                server.ehlo()
                server.starttls(context=tls_context)
                server.ehlo()
            server.login(user, password)
            server.send_message(message)
        return True, "Email sent successfully."
    except (OSError, smtplib.SMTPException, ValueError) as exc:
        logger.exception("SMTP delivery failed")
        return False, str(exc)


def send_email_with_gmail_api(subject, html_content, plain_text=None, attachment=None, reply_to=None):
    """Send MIME email through Gmail's HTTPS API (works on Render Free)."""
    sender, recipient = os.getenv("EMAIL_FROM", "").strip(), os.getenv("EMAIL_TO", "").strip()
    client_id = os.getenv("GMAIL_API_CLIENT_ID", "").strip()
    client_secret = os.getenv("GMAIL_API_CLIENT_SECRET", "").strip()
    refresh_token = os.getenv("GMAIL_API_REFRESH_TOKEN", "").strip()
    if not all([sender, recipient, client_id, client_secret, refresh_token]):
        logger.error("Gmail API delivery is not configured: one or more required settings are missing")
        return False, "Gmail API not configured properly."

    message = EmailMessage()
    message["Subject"], message["From"], message["To"] = subject, sender, recipient
    if reply_to:
        message["Reply-To"] = reply_to
    if plain_text:
        message.set_content(plain_text)
        message.add_alternative(html_content, subtype="html")
    else:
        message.set_content(html_content, subtype="html")
    if attachment:
        filename, content, content_type = attachment
        maintype, subtype = content_type.split("/", 1)
        message.add_attachment(content, maintype=maintype, subtype=subtype, filename=filename)

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/gmail.send"],
        )
        gmail = build("gmail", "v1", credentials=credentials, cache_discovery=False)
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
        gmail.users().messages().send(userId="me", body={"raw": raw_message}).execute()
        return True, "Email sent successfully."
    except Exception as exc:
        logger.exception("Gmail API delivery failed")
        return False, str(exc)


def google_sheets_service():
    """Build a Sheets API client from a service-account JSON env var or file."""
    raw_credentials = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON", "").strip()
    credentials_file = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "").strip()
    if not raw_credentials and not credentials_file:
        raise RuntimeError("Google Sheets credentials are not configured.")
    if raw_credentials:
        info = json.loads(raw_credentials)
    else:
        with open(credentials_file, encoding="utf-8") as credential_file:
            info = json.load(credential_file)
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    credentials = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return build("sheets", "v4", credentials=credentials, cache_discovery=False).spreadsheets()


def read_open_positions():
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "").strip()
    if not spreadsheet_id:
        raise RuntimeError("Google Sheets spreadsheet ID is not configured.")
    value_range = os.getenv("GOOGLE_JOBS_RANGE", "OpenPositions!A:F")
    result = google_sheets_service().values().get(spreadsheetId=spreadsheet_id, range=value_range).execute()
    rows = result.get("values", [])
    if not rows:
        return []
    headers = [str(item).strip().lower().replace(" ", "_") for item in rows[0]]
    positions = []
    for row in rows[1:]:
        values = dict(zip(headers, row))
        if not values.get("title") or str(values.get("active", "true")).strip().lower() not in {"true", "yes", "1", "open", "active"}:
            continue
        positions.append({
            "title": str(values.get("title", "")).strip(),
            "location": str(values.get("location", "")).strip(),
            "employment_type": str(values.get("employment_type", "")).strip(),
            "description": str(values.get("description", "")).strip(),
            "department": str(values.get("department", "")).strip(),
        })
    return positions


def append_sheet_row(value_range, values):
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "").strip()
    if not spreadsheet_id:
        raise RuntimeError("Google Sheets spreadsheet ID is not configured.")
    google_sheets_service().values().append(
        spreadsheetId=spreadsheet_id,
        range=value_range,
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [values]},
    ).execute()


@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    """Provide a lightweight endpoint for uptime and health monitors."""
    return Response(status_code=200)


@app.get("/")
async def index(request: Request):
    return render(request, "index.html")


@app.get("/about")
async def about(request: Request):
    return render(request, "about.html")


@app.get("/services")
async def services(request: Request):
    return render(request, "services.html")


@app.api_route("/attendance", methods=["GET", "POST"])
async def attendance(request: Request):
    return render(request, "attendance.html", title="Attendance")


@app.get("/service/{slug}")
async def service_detail(slug: str, request: Request):
    service = SERVICES.get(slug)
    if service is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Service not found")
    return render(request, "service_detail.html", service=service)


@app.get("/odc")
async def odc(request: Request):
    return render(request, "ODC.html")


@app.get("/value_added_services")
async def value_added_services(request: Request):
    return render(request, "value_added_services.html")


@app.post("/quote")
async def quote(request: Request):
    data = await request.form()
    if not (str(data.get("name", "")).strip() and str(data.get("email", "")).strip()):
        flash(request, "Please provide Name and Email.", "danger")
    else:
        flash(request, "Thank you! Your quote request has been received.", "success")
    return redirect("index", request)


@app.get("/carrier")
async def carrier(request: Request):
    positions, positions_error = [], None
    try:
        positions = await asyncio.to_thread(read_open_positions)
    except Exception:
        logger.exception("Unable to load open positions from Google Sheets")
        positions_error = "We couldn't load open positions right now. Please check back soon or contact our team."
    return render(request, "carrier.html", positions=positions, positions_error=positions_error)


@app.post("/careers/apply")
async def careers_apply(request: Request):
    data = await request.form()
    values = {key: str(data.get(key, "")).strip() for key in ("applicant_name", "applicant_email", "applicant_phone", "desired_role", "cover_letter")}
    resume = data.get("resume_file")
    if not all(values[key] for key in ("applicant_name", "applicant_email", "applicant_phone", "desired_role")):
        flash(request, "Please complete all required application fields.", "danger")
        return redirect("carrier", request)
    if "@" not in values["applicant_email"] or "." not in values["applicant_email"].rsplit("@", 1)[-1]:
        flash(request, "Please enter a valid email address.", "danger")
        return redirect("carrier", request)
    if not isinstance(resume, UploadFile) or not resume.filename:
        flash(request, "Please attach your resume (PDF or DOCX).", "danger")
        return redirect("carrier", request)
    filename = Path(resume.filename).name
    extension = Path(filename).suffix.lower()
    if extension not in {".pdf", ".docx"}:
        flash(request, "Please upload your resume as a PDF or DOCX file.", "danger")
        return redirect("carrier", request)
    resume_content = await resume.read(5 * 1024 * 1024 + 1)
    if not resume_content or len(resume_content) > 5 * 1024 * 1024:
        flash(request, "Your resume must be smaller than 5 MB.", "danger")
        return redirect("carrier", request)
    try:
        positions = await asyncio.to_thread(read_open_positions)
        if values["desired_role"] != "General Application" and values["desired_role"] not in {job["title"] for job in positions}:
            flash(request, "That position is no longer accepting applications. Please choose an open role.", "warning")
            return redirect("carrier", request)
    except Exception:
        logger.exception("Unable to validate application role against Google Sheets")
        flash(request, "Applications are temporarily unavailable. Please contact our team directly.", "danger")
        return redirect("carrier", request)

    timestamp = datetime.now(timezone.utc).isoformat()
    try:
        await asyncio.to_thread(append_sheet_row, os.getenv("GOOGLE_APPLICATIONS_RANGE", "Applications!A:H"), [
            timestamp, values["applicant_name"], values["applicant_email"], values["applicant_phone"],
            values["desired_role"], values["cover_letter"], filename, "New",
        ])
    except Exception:
        logger.exception("Unable to record careers application in Google Sheets")
        flash(request, "We couldn't record your application just now. Please try again shortly or contact our team.", "danger")
        return redirect("carrier", request)

    safe = {key: html.escape(value) for key, value in values.items()}
    body = (f"<h2>New Careers Application</h2><p><b>Name:</b> {safe['applicant_name']}</p>"
            f"<p><b>Email:</b> {safe['applicant_email']}</p><p><b>Phone:</b> {safe['applicant_phone']}</p>"
            f"<p><b>Role:</b> {safe['desired_role']}</p><p><b>Cover letter:</b><br>{safe['cover_letter'] or 'N/A'}</p>"
            f"<p><em>Received at UTC {timestamp}</em></p>")
    sent, info = await asyncio.to_thread(send_email,
        f"Careers application: {values['desired_role']} - {values['applicant_name']}", body,
        plain_text=f"New Careers Application\nName: {values['applicant_name']}\nEmail: {values['applicant_email']}\nPhone: {values['applicant_phone']}\nRole: {values['desired_role']}\nCover letter: {values['cover_letter'] or 'N/A'}\nReceived at UTC {timestamp}",
        attachment=(filename, resume_content, "application/pdf" if extension == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        reply_to=values["applicant_email"],
    )
    if sent:
        flash(request, "Your application has been submitted. Thank you for your interest!", "success")
    else:
        flash(request, "Your application was recorded, but the recruiting email could not be sent. The team can still see it in the applications sheet.", "warning")
    return redirect("carrier", request)


@app.get("/network")
async def network(request: Request):
    locations = [{"city": "Delhi", "type": "Hub"}, {"city": "Mumbai", "type": "Hub"}, {"city": "Bengaluru", "type": "Warehouse"}, {"city": "Chennai", "type": "Warehouse"}]
    return render(request, "network.html", locations=locations)


@app.api_route("/contact", methods=["GET", "POST"])
async def contact(request: Request):
    if request.method == "GET":
        return render(request, "contact.html")
    data = await request.form()
    values = {key: str(data.get(key, "")).strip() for key in ("name", "email", "phone", "company", "city", "service", "subject", "message")}
    if not all(values[key] for key in ("name", "email", "phone")):
        flash(request, "Please provide Name, Email, and Phone.", "danger")
        return redirect("contact", request)
    timestamp = datetime.now(timezone.utc).isoformat()
    with CONTACTS_CSV.open("a", newline="", encoding="utf-8") as file:
        csv.writer(file).writerow([timestamp, values["name"], values["company"], values["email"], values["phone"], values["city"], values["service"], values["message"]])
    safe = {key: html.escape(value) for key, value in values.items()}
    body = f"""<h2>New Contact Enquiry Received</h2><p><b>Name:</b> {safe['name']}</p><p><b>Company:</b> {safe['company'] or 'N/A'}</p><p><b>Email:</b> {safe['email']}</p><p><b>Phone:</b> {safe['phone']}</p><p><b>City:</b> {safe['city'] or 'N/A'}</p><p><b>Service Requested:</b> {safe['service'] or 'N/A'}</p><p><b>Subject:</b> {safe['subject'] or 'N/A'}</p><p><b>Message:</b><br>{safe['message']}</p><p><em>Received at UTC {timestamp}</em></p>"""
    sent, info = await asyncio.to_thread(send_email,
        f"New enquiry from {values['name']} - {values['subject'] or 'General Contact'}", body,
        plain_text=f"New Contact Enquiry Received\nName: {values['name']}\nCompany: {values['company'] or 'N/A'}\nEmail: {values['email']}\nPhone: {values['phone']}\nCity: {values['city'] or 'N/A'}\nService: {values['service'] or 'N/A'}\nSubject: {values['subject'] or 'N/A'}\nMessage: {values['message']}\nReceived at UTC {timestamp}",
        reply_to=values["email"],
    )
    if sent:
        flash(request, "Thank you! Your enquiry has been received.", "success")
    else:
        logger.error("Contact enquiry saved locally but email delivery failed: %s", info)
        flash(request, "Your enquiry was saved, but we couldn't send the email notification. Please contact us directly if your request is urgent.", "warning")
    return redirect("contact", request)


@app.api_route("/register", methods=["GET", "POST"])
async def register(request: Request):
    with SessionLocal() as db:
        if request.session.get("user_id") and db.get(User, request.session["user_id"]):
            return redirect("index", request)
        if request.method == "GET":
            return render(request, "register.html", title="Register", form=RegistrationForm())
        data = await request.form()
        values = {key: str(data.get(key, "")).strip() for key in RegistrationForm.fields}
        errors = {}
        def error(field, message): errors.setdefault(field, []).append(message)
        if not 5 <= len(values["username"]) <= 20: error("username", "Username must be 5-20 characters.")
        for field, label in (("first_name", "First name"), ("last_name", "Last name")):
            if not 1 <= len(values[field]) <= 20: error(field, f"{label} is required (maximum 20 characters).")
        if "@" not in values["email"] or "." not in values["email"].rsplit("@", 1)[-1]: error("email", "Enter a valid email address.")
        if not values["mobile_no"].isdigit() or len(values["mobile_no"]) != 10: error("mobile_no", "Mobile number must contain exactly 10 digits.")
        if not values["password"]: error("password", "Password is required.")
        if values["confirm_password"] != values["password"]: error("confirm_password", "Passwords must match.")
        if not errors:
            if db.scalar(select(User).where(User.username == values["username"])): error("username", "That username is already registered.")
            if db.scalar(select(User).where(User.email == values["email"])): error("email", "That email is already registered.")
            if db.scalar(select(User).where(User.phone_no == values["mobile_no"])): error("mobile_no", "That phone number is already registered.")
        if errors:
            return render(request, "register.html", title="Register", form=RegistrationForm(values, errors))
        user = User(username=values["username"], firstname=values["first_name"], lastname=values["last_name"], email=values["email"], phone_no=values["mobile_no"], password=generate_password_hash(values["password"]))
        db.add(user)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            flash(request, "An account with those details already exists.", "danger")
            return redirect("register", request)
        flash(request, f"Account created successfully for {user.username}! You can now login.", "success")
        return redirect("login", request)


@app.api_route("/login", methods=["GET", "POST"])
async def login(request: Request):
    with SessionLocal() as db:
        user = db.get(User, request.session.get("user_id")) if request.session.get("user_id") else None
        if user:
            return redirect("dashboard", request)
        if request.method == "GET":
            return render(request, "login.html", title="Login", form=LoginForm())
        data = await request.form()
        email, password = str(data.get("email", "")).strip(), str(data.get("password", ""))
        user = db.scalar(select(User).where(User.email == email))
        if user and check_password_hash(user.password, password):
            request.session["user_id"] = user.id
            flash(request, "Logged in successfully.", "success")
            next_page = request.query_params.get("next")
            if next_page and next_page.startswith("/") and not next_page.startswith("//"):
                return RedirectResponse(next_page, status_code=303)
            return redirect("dashboard", request)
        flash(request, "Login unsuccessful. Please check your credentials.", "danger")
        return render(request, "login.html", title="Login", form=LoginForm({"email": email}, {"email": ["Please check your email and password."]}))


def require_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    with SessionLocal() as db:
        return db.get(User, user_id)


@app.get("/dashboard")
async def dashboard(request: Request):
    if not require_user(request):
        return RedirectResponse(str(request.url_for("login")) + "?next=%2Fdashboard", status_code=303)
    stats = {"active_orders": 12, "warehouses": 3, "pending_quotes": 4, "messages": 7}
    return render(request, "dashboard.html", stats=stats)


@app.get("/account")
async def account(request: Request):
    user = require_user(request)
    if not user:
        return RedirectResponse(str(request.url_for("login")) + "?next=%2Faccount", status_code=303)
    return render(request, "account.html", user=user)


@app.get("/ourblog")
async def ourblog(request: Request):
    photo_stories = [
        ("PHOTO-2026-10-24-00-56-19.jpg", "Warehouse team on shift", "AYLB team members in high-visibility workwear, ready for the work on the floor.", "warehouse", "On the floor", "AYLB team members wearing high-visibility vests inside a warehouse."),
        ("PHOTO-2026-10-24-00-56-19_1.jpg", "A blessing for the equipment", "Colleagues take part in a traditional puja beside warehouse equipment.", "culture", "Life at AYLB", "Colleagues perform a puja beside a piece of warehouse equipment."),
        ("PHOTO-2026-10-24-00-56-19_2.jpg", "A warehouse gathering", "Colleagues gather inside the warehouse for a shared occasion.", "culture", "Life at AYLB", "A large group of colleagues gathered inside a warehouse."),
        ("PHOTO-2026-10-24-00-56-19_3.jpg", "Team moment on the warehouse floor", "A group photo with the team among the warehouse shelves.", "warehouse", "On the floor", "AYLB colleagues pose together beside warehouse shelving."),
        ("PHOTO-2026-10-24-00-56-19_4.jpg", "Traditional puja at work", "Colleagues gather for a traditional puja in their workspace.", "culture", "Life at AYLB", "Colleagues take part in a traditional puja in a work area."),
        ("PHOTO-2026-10-24-00-56-19_5.jpg", "A puja with the team", "A small group comes together for a traditional puja in the workplace.", "culture", "Life at AYLB", "Colleagues seated together during a traditional puja."),
        ("PHOTO-2026-10-24-00-56-19_6.jpg", "Team gathering in the warehouse", "Colleagues gather around a speaker for a team address on the warehouse floor.", "warehouse", "On the floor", "Colleagues gathered around a speaker in a warehouse."),
        ("PHOTO-2026-10-24-00-56-19_7.jpg", "A shared celebration", "Colleagues sit together during a traditional workplace gathering.", "culture", "Life at AYLB", "Colleagues seated together at a workplace gathering."),
        ("PHOTO-2026-10-24-00-56-20.jpg", "Puja with the team", "A close view of colleagues taking part in a traditional puja.", "culture", "Life at AYLB", "Colleagues take part in a traditional puja."),
        ("PHOTO-2026-10-24-00-56-20_1.jpg", "Gathered for a traditional ceremony", "Colleagues sit together around a small ceremonial fire.", "culture", "Life at AYLB", "Colleagues seated around a small ceremonial fire."),
        ("PHOTO-2026-10-24-00-56-20_11.jpg", "Holi colors at work", "The team marks Holi with bright colors and a group photo.", "culture", "Life at AYLB", "Colleagues stand together amid colorful Holi decorations."),
        ("PHOTO-2026-10-24-00-56-20_12.jpg", "Independence Day at AYLB", "The team celebrates Independence Day inside the warehouse, surrounded by the tricolor.", "culture", "Life at AYLB", "AYLB colleagues celebrate Independence Day beside a decorated display."),
        ("PHOTO-2026-10-24-00-56-20_13.jpg", "Our warehouse team", "A team photo among the shelves and stock that support day-to-day operations.", "warehouse", "On the floor", "AYLB team members pose among warehouse shelves and stocked goods."),
        ("PHOTO-2026-10-24-00-56-20_2.jpg", "The people behind our operations", "A team photo that celebrates the colleagues who keep work moving.", "team", "Our teams", "AYLB colleagues pose together in workwear."),
        ("PHOTO-2026-10-24-00-56-20_3.jpg", "Preparing for a workplace puja", "Colleagues prepare a space for a traditional puja at work.", "culture", "Life at AYLB", "Colleagues prepare a ceremonial space inside a warehouse."),
        ("PHOTO-2026-10-24-00-56-20_4.jpg", "A puja gathering on the floor", "Colleagues come together for a traditional ceremony in the warehouse.", "culture", "Life at AYLB", "Colleagues gathered around a traditional puja setup in a warehouse."),
        ("PHOTO-2026-10-24-00-56-20_5.jpg", "Team celebration indoors", "Colleagues pose together with celebration badges in their workspace.", "culture", "Life at AYLB", "Colleagues pose together indoors wearing celebration badges."),
        ("PHOTO-2026-10-24-00-56-20_6.jpg", "A team in a new warehouse space", "Colleagues stand together inside a warehouse space, ready for the work ahead.", "warehouse", "On the floor", "AYLB colleagues stand inside a warehouse space."),
        ("PHOTO-2026-10-24-00-56-20_7.jpg", "Holi with the team", "Colleagues mark Holi together with color, rangoli, and a group photo.", "culture", "Life at AYLB", "Colleagues gather outside beside colorful Holi rangoli."),
        ("PHOTO-2026-10-24-00-56-20_8.jpg", "Colleagues at the workplace", "A group photo with colleagues gathered inside their workspace.", "team", "Our teams", "AYLB colleagues stand together inside a workplace."),
        ("PHOTO-2026-10-24-00-56-20_9.jpg", "A big team gathering", "A large group of colleagues comes together inside the warehouse.", "team", "Our teams", "A large group of AYLB colleagues gathered in a warehouse."),
        ("PHOTO-2026-10-24-00-56-20_10.jpg", "A traditional puja in the warehouse", "Colleagues gather around a ceremonial fire for a traditional puja.", "culture", "Life at AYLB", "Colleagues gathered around a ceremonial fire in the warehouse."),
    ]
    posts = [dict(image=image, title=title, description=description, category=category,
                  category_label=category_label, alt=alt)
             for image, title, description, category, category_label, alt in photo_stories]
    return render(request, "ourblog.html", posts=posts)


@app.get("/logout")
async def logout(request: Request):
    request.session.pop("user_id", None)
    flash(request, "You have been logged out.", "info")
    return redirect("index", request)
