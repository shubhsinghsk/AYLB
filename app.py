from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import csv, os, smtplib, ssl
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET', 'change-me')

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
    stats = {'deliveries':'30 Lakh+','warehouses':'12+','on_time':'99%'}
    return render_template('index.html', stats=stats)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/air_freight')
def air_freight():
    return render_template('air_freight.html')

@app.route('/truck_freight')
def truck_freight():
    return render_template('truck_freight.html')

@app.route('/train_freight')
def train_freight():
    return render_template('train_freight.html')

@app.route('/warehousing')
def warehousing():
    return render_template('warehousing.html')

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

@app.route('/industries')
def industries():
    return render_template('industries.html')

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
        name = request.form.get('name','').strip()
        company = request.form.get('company','').strip()
        email = request.form.get('email','').strip()
        phone = request.form.get('phone','').strip()
        city = request.form.get('city','').strip()
        service = request.form.get('service','').strip()
        message = request.form.get('message','').strip()

        if not (name and email and phone):
            flash('Please provide Name, Email, and Phone.', 'danger')
            return redirect(url_for('contact'))

        timestamp = datetime.utcnow().isoformat()
        with open(CONTACTS_CSV, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp,name,company,email,phone,city,service,message])

        subject = f'New enquiry from {name} - {service or "General"}'
        html = f"""
        <h2>New enquiry received</h2>
        <p><b>Name:</b> {name}</p>
        <p><b>Company:</b> {company}</p>
        <p><b>Email:</b> {email}</p>
        <p><b>Phone:</b> {phone}</p>
        <p><b>City:</b> {city}</p>
        <p><b>Service:</b> {service}</p>
        <p><b>Message:</b><br>{message}</p>
        <p><em>Received at UTC {timestamp}</em></p>
        """

        sent, info = send_email(subject, html)
        if sent:
            flash('Thank you! Your enquiry has been received.', 'success')
        else:
            flash('Message saved, but failed to send email. ' + info, 'warning')

        return redirect(url_for('contact'))

    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
