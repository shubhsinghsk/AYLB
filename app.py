from flask import Flask, render_template, request, redirect, url_for, flash, abort
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
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')


# --- Service detail mapping and route ---------------------------------
# A single route powers all service pages referenced from templates/services.html
SERVICES = {
    # Business / Tech services
    'wms-software': {
        'slug': 'wms-software',
        'title': 'WMS & E-commerce Software',
        'description': 'Unified platform for inventory, orders, and sales channel integration.',
        'long_description': 'A Warehouse Management System (WMS) that integrates inventory control, order routing, and sales channel synchronization. Supports barcode scanning, API integrations with marketplaces and couriers, and real-time stock visibility.',
        'images': ['services/wms-1.jpg', 'services/wms-2.jpg']
    },
    'fulfillment-lastmile': {
        'slug': 'fulfillment-lastmile',
        'title': 'Fulfillment & Last Mile',
        'description': 'End-to-end execution from picking to customer doorstep delivery.',
        'long_description': 'We optimise picking, packing and final-mile delivery with route optimisation and partner carriers to reduce cost and improve delivery times.',
        'images': ['services/fulfillment-1.jpg']
    },
    'technology-autonomous': {
        'slug': 'technology-autonomous',
        'title': 'Technology Autonomous',
        'description': 'Future-proof your operations with robotics, AI, and process automation.',
        'long_description': 'Solution design and deployment of robotics, AGVs, and automation workflows to increase throughput and improve labour utilisation.',
        'images': []
    },

    # 3PL / Operations services (slugs generated the same way as in the template)
    'warehouse-services': {'slug':'warehouse-services','title':'Warehouse Services','description':'Multi-client and dedicated warehousing solutions for inventory storage and management.','long_description':'Secure storage, inventory rotation and SLA-driven handling for B2B and B2C goods.','images':['services/warehouse-1.png','services/warehouse-2.png']},
    'contract-logistics': {'slug':'contract-logistics','title':'Contract Logistics','description':'Long-term logistics partnerships including managed operations and SLAs.','long_description':'Managed operations where we run all warehouse functions under long-term contracts with agreed KPIs.','images':[]},
    'fulfillment-warehouse': {'slug':'fulfillment-warehouse','title':'Fulfillment Warehouse','description':'Fulfilment centres optimized for fast e-commerce order throughput.','long_description':'High-throughput fulfilment centres with specialised packing, labelling and channel-specific workflows.','images':['services/fulfillment-warehouse.jpg']},
    'on-demand-warehousing': {'slug':'on-demand-warehousing','title':'On-Demand Warehousing','description':'Flexible short-term storage and space-on-demand for seasonal peaks.','long_description':'Hourly/daily/weekly warehousing options to handle peak seasons or overflow stock.','images':[]},
    'distribution-and-transportation': {'slug':'distribution-and-transportation','title':'Distribution & Transportation','description':'Networked distribution and transport planning for timely deliveries.','long_description':'Fleet and carrier management for efficient intercity and last-mile distribution.','images':[]},
    'order-management-service': {'slug':'order-management-service','title':'Order Management Service','description':'Centralised order orchestration across channels and warehouses.','long_description':'Consolidation of marketplace and webstore orders with smart routing to fulfilment points.','images':[]},
    'e-commerce-warehouse-services': {'slug':'e-commerce-warehouse-services','title':'E-commerce Warehouse Services','description':'Dedicated flows for marketplace and direct-to-consumer fulfilment.','long_description':'SLA-focused ecommerce handling including returns and replacements.','images':[]},
    'value-added-service': {'slug':'value-added-service','title':'Value Added Service','description':'Kitting, labelling, custom packaging and other value-add operations.','long_description':'Custom packaging, assembly and labelling services to enhance your product presentation.','images':[]},
    'third-party-logistics-3pl': {'slug':'third-party-logistics-3pl','title':'Third Party Logistics (3PL)','description':'End-to-end outsourced logistics management and execution.','long_description':'Full logistics outsourcing including warehouse operations, transport and customer support.','images':[]},
    'reverse-logistics-services': {'slug':'reverse-logistics-services','title':'Reverse Logistics Services','description':'Returns handling, refurbishment and disposition services.','long_description':'End-to-end returns management with classification, refurbishment and disposition.','images':[]},
    'warehouse-management-system': {'slug':'warehouse-management-system','title':'Warehouse Management System','description':'Software and integrations to operate warehouses efficiently.','long_description':'Integrated WMS that ties in with carriers, marketplaces and accounting systems.','images':[]},
    'education-and-training-solutions': {'slug':'education-and-training-solutions','title':'Education & Training Solutions','description':'Training programs to upskill warehouse and operations teams.','long_description':'On-site and remote training modules for operational best practices and safety.','images':[]},
}


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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
