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
    # Business / Tech Services
    'wms-software': {
        'slug': 'wms-software',
        'title': 'WMS & E-commerce Software',
        'description': 'Unified control for inventory, warehouse, and orders across all sales channels.',
        'long_description': (
            'Achieve 99.9% inventory accuracy with real-time, scanner-guided workflows such as Smart Putaway and Picking. '
            'Our system provides a unified view of stock across all locations, ensuring centralized order management and intelligent routing. '
            'Seamlessly integrates with Shopify, Amazon, ERP systems, and courier partners for instant stock sync and tracking updates.'
        ),
        'images': ['services/wms1.png', 'services/wms.png'],
        'features': [
            'Real-time inventory visibility (single view across locations)',
            '99.9% inventory accuracy via scanner-guided workflows',
            'Smart putaway & picking workflows',
            'Centralized Order Management & intelligent routing',
            'Out-of-the-box connectors (Shopify, Amazon, major ERPs)',
            'Bi-directional stock and tracking sync',
            'Barcode & mobile scanning support'
        ]
    },

    'fulfillment-lastmile': {
        'slug': 'fulfillment-lastmile',
        'title': 'Fulfillment & Last Mile',
        'description': 'Seamless delivery management from warehouse pick to customer doorstep.',
        'long_description': (
            'Our fulfillment solution ensures complete visibility and precision from order picking to last-mile delivery. '
            'With optimized routing, real-time tracking, and partner integration, we deliver fast, cost-effective, and reliable service—every time.'
        ),
        'images': ['services/Fulfillment & Last Mile.png'],
        'features': [
            'End-to-end execution from pick to doorstep',
            'Route optimisation for fastest & cheapest delivery',
            'Real-time shipment tracking and ETA updates',
            'Carrier partner integrations and multi-carrier support',
            'Proof-of-delivery and delivery exception handling'
        ]
    },

    'technology-autonomous': {
        'slug': 'technology-autonomous',
        'title': 'Technology & Autonomy',
        'description': 'AI, robotics, and automation to future-proof your logistics operations.',
        'long_description': (
            'Transform operations from reactive to predictive using AI, robotics, and process automation. '
            'Automate warehouse workflows, from putaway to packing, and integrate with AGVs and smart sensors for maximum throughput. '
            'AI-driven inventory placement, vision-based automation, and intelligent routing reduce human error and boost productivity.'
        ),
        'images': ['services/Technology Autonomous.png'],
        'features': [
            'AI-powered decisions (predictive placement & routing)',
            'Robotics & AGV integration (robot communication layer)',
            'Vision technology and smart sensors for hands-free tasks',
            'Process automation for putaway, picking, and packing',
            'Automated exception detection and corrective actions'
        ]
    },

    # 3PL / Operational Services
    'warehouse-services': {
        'slug': 'warehouse-services',
        'title': 'Warehouse Services',
        'description': 'Flexible multi-client and dedicated warehousing for any business scale.',
        'long_description': (
            'Choose between shared multi-client or exclusive dedicated storage models. '
            'Multi-client warehouses provide cost-efficient, scalable space for SMEs, while dedicated setups offer full control and customization for large enterprises. '
            'Both ensure secure handling, space optimization, and speed-to-market advantage.'
        ),
        'images': ['services/warehouse-1.png', 'services/warehouse-2.png'],
        'features': [
            'Multi-client (shared) & dedicated (contract) models',
            'Flexible SLAs and scalable space allocation',
            'Secure storage and inventory rotation',
            'Slotting & space optimisation',
            'Rapid onboarding and speed-to-market facilities'
        ]
    },

    'contract-logistics': {
        'slug': 'contract-logistics',
        'title': 'Contract Logistics',
        'description': 'Long-term strategic outsourcing of warehouse and transport operations.',
        'long_description': (
            'Comprehensive logistics management through long-term contracts backed by SLAs and KPIs. '
            'We manage inventory, distribution, and fulfillment as an integrated extension of your business—allowing you to focus on core growth while reducing fixed costs.'
        ),
        'images': ['services/Contract Logistics.png'],
        'features': [
            'Managed end-to-end operations as an extension of your team',
            'SLA-driven performance with KPI monitoring (OTD, accuracy)',
            'Long-term planning and cost conversion from fixed to variable',
            'Custom workflows and reporting'
        ]
    },

    'fulfillment-warehouse': {
        'slug': 'fulfillment-warehouse',
        'title': 'Fulfillment Warehouse',
        'description': 'High-speed e-commerce fulfillment designed for modern order volumes.',
        'long_description': (
            'Specialized fulfillment centers handle every post-purchase operation—receiving, storing, picking, packing, and shipping. '
            'With WMS-driven automation and optimized slotting, we ensure fast, accurate, and scalable order processing.'
        ),
        'images': ['services/Fulfillment Warehouse.png'],
        'features': [
            'High-speed pick, pack & ship operations',
            'Efficient receiving and optimized slotting',
            'Small-order throughput optimisation for e-commerce',
            'WMS-driven accuracy and automation',
            'Scalable labour & peak handling'
        ]
    },

    'on-demand-warehousing': {
        'slug': 'on-demand-warehousing',
        'title': 'On-Demand Warehousing',
        'description': 'Flexible storage and workforce solutions for seasonal or overflow needs.',
        'long_description': (
            'Scale your logistics footprint on demand—pay only for the space and labor you use. '
            'Perfect for managing seasonal peaks, promotional surges, or inventory overflow without long-term commitments.'
        ),
        'images': ['services/On-Demand Warehousing.png'],
        'features': [
            'Hourly/daily/weekly warehousing options',
            'Pay-as-you-use pricing model',
            'Rapid scale-up and scale-down for peaks',
            'Temporary workforce & operational support'
        ]
    },

    'distribution-and-transportation': {
        'slug': 'distribution-and-transportation',
        'title': 'Distribution & Transportation',
        'description': 'Optimized transport and delivery network for efficiency and reliability.',
        'long_description': (
            'We design optimized routes, manage carrier networks, and ensure timely deliveries across intercity and last-mile networks. '
            'Our focus areas include route optimization, visibility, and reliability for every shipment.'
        ),
        'images': ['services/Distribution & Transportation.png'],
        'features': [
            'Strategic route planning and optimisation',
            'Fleet & carrier management',
            'Delivery tracking and performance metrics',
            'Network design for cost & time efficiency'
        ]
    },

    'order-management-service': {
        'slug': 'order-management-service',
        'title': 'Order Management Service',
        'description': 'Centralized orchestration of orders across channels and fulfillment nodes.',
        'long_description': (
            'Our OMS consolidates all marketplace and D2C orders into a single dashboard. '
            'It intelligently routes each order to the optimal fulfillment point for fastest and most cost-efficient delivery.'
        ),
        'images': ['services/Order Management Service.png'],
        'features': [
            'Centralized order orchestration across channels',
            'Real-time order sync and consolidated view',
            'Intelligent routing to optimal fulfillment point',
            'Order prioritisation, splitting & batching'
        ]
    },

    'e-commerce-warehouse-services': {
        'slug': 'e-commerce-warehouse-services',
        'title': 'E-commerce Warehouse Services',
        'description': 'Fast, compliant fulfillment tailored for online retail operations.',
        'long_description': (
            'Dedicated warehouse flows for both Direct-to-Consumer and Marketplace fulfillment. '
            'We handle packaging, labeling, and compliance with channel-specific standards like Amazon and Walmart, ensuring accuracy and customer satisfaction.'
        ),
        'images': ['services/E-commerce Warehouse Services.png'],
        'features': [
            'DTC and marketplace-specific fulfillment flows',
            'Packaging, labelling and channel compliance (Amazon/Walmart)',
            'Returns-ready workflows and fast replacements',
            'Performance monitoring to protect seller ratings'
        ]
    },

    'value-added-service': {
        'slug': 'value-added-service',
        'title': 'Value Added Services',
        'description': 'Enhance your product presentation with kitting, bundling, and labeling.',
        'long_description': (
            'We provide in-warehouse customization like kitting, bundling, labeling, returns handling, and quality checks. '
            'These services ensure your products are market-ready while optimizing cost and personalization.'
        ),
        'images': ['services/Value Added Service.png'],
        'features': [
            'Kitting, bundling and custom packaging',
            'Labeling, barcoding and SKU prep',
            'Quality control checks and market-readiness',
            'Pre-distribution customization to reduce downstream costs'
        ]
    },

    'third-party-logistics-3pl': {
        'slug': 'third-party-logistics-3pl',
        'title': 'Third Party Logistics (3PL)',
        'description': 'Comprehensive logistics outsourcing for end-to-end efficiency.',
        'long_description': (
            'We act as a true extension of your supply chain, managing warehousing, transportation, and fulfillment under one roof. '
            'Our technology-driven 3PL solutions deliver scalability, cost efficiency, and top-tier service quality.'
        ),
        'images': ['services/Third Party Logistics (3PL).png'],
        'features': [
            'End-to-end logistics outsourcing (warehousing + transport)',
            'Integrated technology & reporting',
            'Scalable operations and network leverage',
            'Dedicated account & SLA governance'
        ]
    },

    'reverse-logistics-services': {
        'slug': 'reverse-logistics-services',
        'title': 'Reverse Logistics Services',
        'description': 'Returns management, refurbishment, and product recovery made simple.',
        'long_description': (
            'We handle every stage of product returns—from receipt and inspection to refurbishment, recycling, or liquidation. '
            'Our process maximizes recovery value, minimizes waste, and enhances customer satisfaction through fast, transparent returns handling.'
        ),
        'images': ['services/Reverse Logistics Services.png'],
        'features': [
            'Returns intake, inspection & triage',
            'Refurbishment and repair workflows',
            'Disposition planning: restock, liquidate, recycle',
            'Value recovery analytics and reporting'
        ]
    },

    'warehouse-management-system': {
        'slug': 'warehouse-management-system',
        'title': 'Warehouse Management System',
        'description': 'Software to streamline, track, and optimize all warehouse operations.',
        'long_description': (
            'Our WMS provides real-time visibility into inventory, labor, and space utilization. '
            'It manages receiving, putaway, picking, packing, and shipping with precision, reducing costs and improving throughput.'
        ),
        'images': ['services/Warehouse Management System.png'],
        'features': [
            'Receiving & putaway orchestration',
            'Inventory control and location management',
            'Picking & packing optimisation',
            'Shipping label generation and carrier handoffs',
            'Labor tracking & productivity dashboards'
        ]
    },

    'education-and-training-solutions': {
        'slug': 'education-and-training-solutions',
        'title': 'Education & Training Solutions',
        'description': 'Upskill warehouse and logistics teams for better performance and safety.',
        'long_description': (
            'We offer structured training programs covering warehouse operations, WMS usage, safety protocols, and leadership. '
            'Our training reduces errors, improves accuracy, and fosters a skilled, motivated workforce aligned with your operational goals.'
        ),
        'images': ['services/Education & Training Solutions.png'],
        'features': [
            'Custom training modules for WMS and OMS usage',
            'Operational best-practices and safety training',
            'On-site and remote learning options',
            'Certification programs and skill assessments'
        ]
    },
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
