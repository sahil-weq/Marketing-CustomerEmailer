import requests
import json
import html
import re
import logging
import markdown


# Airtable API credentials and URL
# API_KEY = os.getenv('API_KEY')# Replace with your Airtable API key
# BASE_ID = os.getenv('BASE_ID') # Your Airtable Base ID
# AISENSY_API_KEY = os.getenv('AISENSY_API_KEY')# API key for WhatsApp authentication.
# ZOHO_API_KEY = os.getenv('AISENSY_API_KEY')# API key for Zoho ZeptoMail authentication.

API_KEY = "patqi7T4XLXXxUs2i.eba91528e22c97230f1833a1b4bd605f8e02cf47092b89e1018c388634828647"
BASE_ID = "appy8Yts8O6ZV2rks"
AISENSY_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY2YTc5ZmZiOWY4MWJmMGI3NzhjZWUxZCIsIm5hbWUiOiJXRVEgVGVjaG5vbG9naWVzIiwiYXBwTmFtZSI6IkFpU2Vuc3kiLCJjbGllbnRJZCI6IjY2YTc5ZmZiOWY4MWJmMGI3NzhjZWUwZSIsImFjdGl2ZVBsYW4iOiJCQVNJQ19NT05USExZIiwiaWF0IjoxNzIyMjYxNDk5fQ.8suQQc0pO-vT0N6C9KUpccM0-L4GaC9ilZ2-sSQOlZY"
ZOHO_API_KEY = "Zoho-enczapikey PHtE6r0ME7zrg2N9oEVW5aDqQs+hZ4kr9OIzKgdOsN1LXqRSH01TqYwvkjS0/R95XPgXHKHIm4s+s7qYt7iFdG7kNjofXWqyqK3sx/VYSPOZsbq6x00etlsackHdUoDqcdJo1CzRu93YNA=="

headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

logging.basicConfig(filename='app.log', level=logging.DEBUG)

# Function definitions remain mostly the same
def get_airtable_data():
    TABLE_NAME = 'Customers'
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}'
    params = {"maxRecords": 10, "view": "Grid view"}
    all_records = []

    while True:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            all_records.extend(data['records'])
            if 'offset' in data:
                params['offset'] = data['offset']
            else:
                break
        else:
            logging.info(f"Error: {response.status_code}, Message: {response.text}")
            break

    return all_records

def get_airtable_emailtemplate(template_id):
    TABLE_NAME = 'Templates'
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}/{template_id}'
    response = requests.get(url, headers=headers)
    response_data = response.json()
    return response_data.get("fields", {})

def get_airtable_watemplate(template_id):
    TABLE_NAME = 'Templates'
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}/{template_id}'
    response = requests.get(url, headers=headers)
    response_data = response.json()
    return response_data.get("fields", {}).get("Template Name", "")

def convert_to_html(text):
    escaped_text = html.escape(text)
    html_formatted = escaped_text.replace("\n", "<br>")
    return f"""
    <html>
        <body>
            <div style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6;">
                {html_formatted}
            </div>
        </body>
    </html>
    """

def convert_markdown_to_html(text):
    html_formatted = markdown.markdown(text)
    return f"""
    <html>
        <body>
            <div style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6;">
                {html_formatted}
            </div>
        </body>
    </html>
    """


def validate_and_format_phone(phone_number):
    if re.fullmatch(r"91\d{10}", phone_number):
        return f"+{phone_number}"
    elif re.fullmatch(r"\d{10}", phone_number):
        return f"+91{phone_number}"
    else:
        logging.info(f"Invalid phone number: {phone_number}")
        return None

def send_email_to_customer(cust_data, subject, email_html):    
    full_name = f"{cust_data.get('first_name')} {cust_data.get('last_name')}" if cust_data.get('last_name') else cust_data.get('first_name')

    payload = {
        "from": {"address": "campaign@weqtech.com", "name" : "WEQ Technologies"},
        "to": [{"email_address": {"address": cust_data.get('email'), "name": full_name}}],
        "subject": subject,
        "htmlbody": email_html,
        "reply_to": {"address": "sales@weqtechnologies.com"}
    }
    response = requests.post(
        "https://api.zeptomail.in/v1.1/email",
        headers={
            'Authorization': ZOHO_API_KEY,
            'Content-Type': 'application/json'
        },
        data=json.dumps(payload)
    )
    if response.status_code == 200:
        logging.info(f"Email sent to {cust_data.get('email')}")
    else:
        logging.info(f"Error: {response.status_code}, Message: {response.text}")

def send_whatsapp_message(campaign_name, first_name, phone_number):
    destination = validate_and_format_phone(phone_number)
    if not phone_number or not first_name or not destination:
        return "Missing required details for customer"

    payload = {
        "apiKey": AISENSY_API_KEY,
        "campaignName": campaign_name,
        "destination": destination,
        "userName": first_name,
        "source": "AWS Lambda",
        "templateParams": [first_name]
    }
    response = requests.post(
        "https://backend.aisensy.com/campaign/t1/api/v2",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    if response.status_code == 200:
        logging.info(f"WhatsApp message sent successfully to {first_name} ({phone_number})")
    else:
        logging.info(f"Failed to send WhatsApp message. Status: {response.status_code}, Response: {response.text}")

# Lambda handler function
# def lambda_handler(event, context):
def lambda_handler():
    records = get_airtable_data()
    logging.info(f"=======Script Running for {len(records)} records from AirTable")
    if records:
        for record in records:
            fields = record['fields']
            
            cust_data = {
                "first_name" : fields.get('First Name'),
                "last_name" : fields.get('Last Name'),
                "email" : fields.get('Email Address'),
                "company" : fields.get('Company Name'),
                "phone_number" : fields.get('Phone Number'),
                "email_template_id" : fields.get('Template Selected', ['No Template'])[0],
                "whatsapp_campaign_id" : fields.get('WhatsApp Template Selected', ['No Template'])[0]
            }
            
            if cust_data.get('email_template_id') and fields.get('Should Send Email'):
                email_data = get_airtable_emailtemplate(cust_data.get('email_template_id'))
                logging.info(email_data)

                email_data['Email Body'] = email_data['Email Body'].replace("[FirstName]", cust_data.get('first_name') or "Partner")
                email_data['Email Body'] = email_data['Email Body'].replace("[LastName]", cust_data.get('last_name') or "")
                email_data['Email Body'] = email_data['Email Body'].replace("[CompanyName]", cust_data.get('company') or "your firm")
                
                email_data['Email Subject'] = email_data['Email Subject'].replace("[FirstName]", cust_data.get('first_name') or "Partner")
                email_data['Email Subject'] = email_data['Email Subject'].replace("[LastName]", cust_data.get('last_name') or "")
                email_data['Email Subject'] = email_data['Email Subject'].replace("[CompanyName]", cust_data.get('company') or "your firm")

                #  Convert to HTML
                email_html = convert_markdown_to_html(email_data['Email Body'])

                # logging.info(json.dumps(email_data))
                if email_data['Email Body'] and cust_data['email']:
                    send_email_to_customer(
                        cust_data, 
                        email_data['Email Subject'],
                        email_html
                    )

            if cust_data.get('whatsapp_campaign_id') and fields.get('Should Send Whatsapp Message'):
                wa_campaign = get_airtable_watemplate(cust_data.get('whatsapp_campaign_id'))

                if wa_campaign:
                    send_whatsapp_message(
                        wa_campaign, 
                        cust_data.get('first_name'),
                        cust_data.get('phone_number')
                    )


lambda_handler()
