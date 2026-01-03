from flask import Flask, render_template, request, redirect, url_for, flash, abort
from datetime import datetime
from AYLB_LOGIS import app, db,bcrypt
import csv, os, smtplib, ssl
from email.message import EmailMessage
from dotenv import load_dotenv
from AYLB_LOGIS.form import RegistrationForm, LoginForm
from werkzeug.security import generate_password_hash, check_password_hash
from AYLB_LOGIS.models import User
from AYLB_LOGIS import config
from flask_login import login_user, current_user, logout_user, login_required
import requests
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime


SERVICES = config.SERVICES

CONTACTS_CSV = 'contacts.csv'
if not os.path.exists(CONTACTS_CSV):
    with open(CONTACTS_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp','name','company','email','phone','city','service','message'])

def send_email(subject, html_content, plain_text=None):
    host = os.getenv('SMTP_HOST')
    port = int(os.getenv('SMTP_PORT','587'))
    user = os.getenv('SMTP_USERNAME')
    password = os.getenv('SMTP_PASSWORD')
    sender = os.getenv('EMAIL_FROM')
    recipient = os.getenv('EMAIL_TO')

    if not all([host, port, user, password, sender, recipient]):
        return False, 'SMTP not configured properly.'

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient
    if plain_text:
        msg.set_content(plain_text)
        msg.add_alternative(html_content, subtype='html')
    else:
        msg.set_content(html_content, subtype='html')

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(host, port, timeout=10) as server:
            server.starttls(context=context)
            server.login(user, password)
            server.send_message(msg)
        return True, 'Email sent successfully.'
    except Exception as e:
        return False, str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

# GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzvuob2ZyQ2Gf1Q5StrhOxaM-pMSnB2Mtw3Y8629H8FjOpUWU3SOWdGaMSc3zYqQLiS7Q/exec"

# def calculate_distance(lat1, lon1, lat2, lon2):
#     R = 6371000
#     dlat = radians(lat2 - lat1)
#     dlon = radians(lon2 - lon1)

#     a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
#     c = 2 * atan2(sqrt(a), sqrt(1 - a))
#     return R * c

@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    # if request.method == 'POST':
    #     data = request.form

    #     name = data.get('name')
    #     empid = data.get('empid')
    #     punch = data.get('punch')
    #     auto_lat, auto_lon = map(float, data.get('location').split(','))
    #     manual_name, manual_lat, manual_lon = data.get('manual_location').split(',')

    #     distance = round(
    #         calculate_distance(
    #             auto_lat, auto_lon,
    #             float(manual_lat), float(manual_lon)
    #         )
    #     )

    #     is_mismatch = distance > 200

    #     payload = {
    #         'name': name,
    #         'empid': empid,
    #         'email': data.get('email', 'attendance@aylb.com'),  # REQUIRED
    #         'punch': punch,
    #         'manual_location': manual_name,
    #         'location': f"{auto_lat},{auto_lon}",
    #         'distance': distance,          # REQUIRED
    #         'status': 'FLAGGED' if is_mismatch else 'OK',
    #         'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #     }

        
    #     try:
    #         requests.post(
    #         GOOGLE_SCRIPT_URL,
    #         data=payload,   # ⚠️ IMPORTANT (NOT json=payload)
    #         timeout=10
    #         )

    #         flash(f'{punch} recorded successfully!', 'success')
    #     except Exception:
    #         flash('Attendance submission failed.', 'danger')

    #     if distance > 200:
    #         flash('Location mismatch detected (outside 200m). Marked for review.', 'warning')

    #     return redirect(url_for('attendance'))

    return render_template('attendance.html', title="Attendance")



# --- Service detail mapping and route ---------------------------------
# A single route powers all service pages referenced from templates/services.html


@app.route('/service/<slug>')
def service_detail(slug):
    service = SERVICES.get(slug)
    if not service:
        # If slug not found, return a 404
        abort(404)
    return render_template('service_detail.html', service=service)


@app.route('/odc')
def odc():
    return render_template('ODC.html')

@app.route('/value_added_services')
def value_added_services():
    return render_template('value_added_services.html')

@app.route('/quote', methods=['POST'])
def quote():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        email = request.form.get('email','').strip()
        message = request.form.get('message','').strip()

        if not (name and email):
            flash('Please provide Name and Email.', 'danger')
            return redirect(url_for('index'))

        # Send email logic here
        flash('Thank you! Your quote request has been received.', 'success')
        return redirect(url_for('index'))

@app.route('/carrier')
def carrier():
    return render_template('carrier.html')

@app.route('/network')
def network():
    locations = [
        {'city':'Delhi','type':'Hub'},
        {'city':'Mumbai','type':'Hub'},
        {'city':'Bengaluru','type':'Warehouse'},
        {'city':'Chennai','type':'Warehouse'},
    ]
    return render_template('network.html', locations=locations)

@app.route('/contact', methods=['GET','POST'])
def contact():
    if request.method == 'POST':
        # Fields expected by the CSV/Email template:
        name = request.form.get('name','').strip()
        email = request.form.get('email','').strip()
        phone = request.form.get('phone','').strip()
        
        # Fields not present in the current HTML form (set to default empty strings)
        company = request.form.get('company','').strip()
        city = request.form.get('city','').strip()
        service = request.form.get('service','').strip()
        
        # Fields present in the current HTML form
        subject = request.form.get('subject','').strip()
        message = request.form.get('message','').strip()

        if not (name and email and phone):
            flash('Please provide Name, Email, and Phone.', 'danger')
            return redirect(url_for('contact'))

        timestamp = datetime.utcnow().isoformat()
        
        # 1. Log to CSV (uses all expected fields)
        with open(CONTACTS_CSV, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Row fields: ['timestamp','name','company','email','phone','city','service','message']
            writer.writerow([timestamp,name,company,email,phone,city,service,message])

        # 2. Prepare and send email (uses subject from the form)
        
        # Use subject from form if provided, otherwise create a default subject
        email_subject = f'New enquiry from {name} - {subject or "General Contact"}'
        
        html = f"""
        <h2>New Contact Enquiry Received</h2>
        <p><b>Name:</b> {name}</p>
        <p><b>Company:</b> {company if company else 'N/A'}</p>
        <p><b>Email:</b> {email}</p>
        <p><b>Phone:</b> {phone}</p>
        <p><b>City:</b> {city if city else 'N/A'}</p>
        <p><b>Service Requested:</b> {service if service else 'N/A'}</p>
        <p><b>Subject:</b> {subject if subject else 'N/A'}</p>
        <p><b>Message:</b><br>{message}</p>
        <p><em>Received at UTC {timestamp}</em></p>
        """

        sent, info = send_email(email_subject, html)
        if sent:
            flash('Thank you! Your enquiry has been received.', 'success')
        else:
            # Displays the specific SMTP error for debugging
            flash('Message saved, but failed to send email. Check SMTP settings. Error: ' + info, 'warning') 

        return redirect(url_for('contact'))

    return render_template('contact.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # Hash the password before storing
        hashed_password = generate_password_hash(form.password.data)
        
        

        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            firstname = form.first_name.data,
            lastname = form.last_name.data,
            phone_no=int(form.mobile_no.data),
            password=hashed_password
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            flash(f'Account created successfully for {form.username.data}! You can now login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating account: {str(e)}', 'danger')
    
    return render_template('register.html', title='Register', form=form)


# --- login route (update redirect to dashboard) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            flash('Logged in successfully.', 'success')
            # next param handling (optional)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Login unsuccessful. Please check your credentials.', 'danger')

    return render_template('login.html', title='Login', form=form)


# --- dashboard (protected) ---
@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    # Example dashboard data (replace with real queries later)
    stats = {
        'active_orders': 12,
        'warehouses': 3,
        'pending_quotes': 4,
        'messages': 7,
        # you can add badges like unread_messages etc.
    }
    return render_template('dashboard.html', stats=stats)


# --- account/profile (protected) ---
@app.route('/account', methods=['GET'])
@login_required
def account():
    # current_user is provided by flask-login
    return render_template('account.html', user=current_user)


# --- our blog (public) ---
@app.route('/ourblog', methods=['GET'])
def ourblog():
    # stubbed posts - replace with DB query later
    posts = [
        {'title': 'How to optimize last-mile delivery', 'slug':'last-mile'},
        {'title': 'Warehouse automation trends 2025', 'slug':'automation-2025'},
    ]
    return render_template('ourblog.html', posts=posts)


# --- logout (fix decorator order) ---
@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')
