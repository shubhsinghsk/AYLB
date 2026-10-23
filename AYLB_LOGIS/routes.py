"""Website routes implemented with FastAPI and Starlette sessions."""

import csv
import html
import os
import smtplib
import ssl
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from AYLB_LOGIS import PACKAGE_DIR, PROJECT_DIR, SessionLocal, app
from AYLB_LOGIS.config import SERVICES
from AYLB_LOGIS.form import LoginForm, RegistrationForm
from AYLB_LOGIS.models import User

templates = Jinja2Templates(directory=PACKAGE_DIR / "templates")
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


def send_email(subject, html_content, plain_text=None):
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user, password = os.getenv("SMTP_USERNAME"), os.getenv("SMTP_PASSWORD")
    sender, recipient = os.getenv("EMAIL_FROM"), os.getenv("EMAIL_TO")
    if not all([host, user, password, sender, recipient]):
        return False, "SMTP not configured properly."
    message = EmailMessage()
    message["Subject"], message["From"], message["To"] = subject, sender, recipient
    if plain_text:
        message.set_content(plain_text)
        message.add_alternative(html_content, subtype="html")
    else:
        message.set_content(html_content, subtype="html")
    try:
        with smtplib.SMTP(host, port, timeout=10) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(user, password)
            server.send_message(message)
        return True, "Email sent successfully."
    except (OSError, smtplib.SMTPException) as exc:
        return False, str(exc)


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
    return render(request, "carrier.html")


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
    sent, info = send_email(f"New enquiry from {values['name']} - {values['subject'] or 'General Contact'}", body)
    if sent:
        flash(request, "Thank you! Your enquiry has been received.", "success")
    else:
        flash(request, "Message saved, but failed to send email. Check SMTP settings. Error: " + info, "warning")
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
    posts = [{"title": "How to optimize last-mile delivery", "slug": "last-mile"}, {"title": "Warehouse automation trends 2025", "slug": "automation-2025"}]
    return render(request, "ourblog.html", posts=posts)


@app.get("/logout")
async def logout(request: Request):
    request.session.pop("user_id", None)
    flash(request, "You have been logged out.", "info")
    return redirect("index", request)
