import requests
import json
import html
import re
import os

# Airtable API credentials and URL
API_KEY = os.environ['API_KEY']# Replace with your Airtable API key
BASE_ID = os.environ['BASE_ID'] # Your Airtable Base ID
AISENSY_API_KEY = os.environ['AISENSY_API_KEY']# API key for WhatsApp authentication.

headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

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
            print(f"Error: {response.status_code}, Message: {response.text}")
            break

    return all_records

def get_airtable_template(template_id):
    TABLE_NAME = 'Templates'
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}/{template_id}'
    response = requests.get(url, headers=headers)
    response_data = response.json()
    return response_data.get("fields", {}).get("Email Body", "")

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

def validate_and_format_phone(phone_number):
    if re.fullmatch(r"91\d{10}", phone_number):
        return f"+{phone_number}"
    elif re.fullmatch(r"\d{10}", phone_number):
        return f"+91{phone_number}"
    else:
        print(f"Invalid phone number: {phone_number}")
        return None

def send_email_to_customer(first_name, email, email_template):
    email_html = convert_to_html(email_template)
    payload = {
        "from": {"address": "noreply@weqtech.com"},
        "to": [{"email_address": {"address": email, "name": first_name}}],
        "subject": "Your Custom Email",
        "htmlbody": email_html
    }
    response = requests.post(
        "https://api.zeptomail.in/v1.1/email",
        headers={
            'Authorization': 'Zoho-enczapikey your_zepto_mail_key',
            'Content-Type': 'application/json'
        },
        data=json.dumps(payload)
    )
    if response.status_code == 200:
        print(f"Email sent to {email}")
    else:
        print(f"Error: {response.status_code}, Message: {response.text}")

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
        print(f"WhatsApp message sent successfully to {first_name} ({phone_number})")
    else:
        print(f"Failed to send WhatsApp message. Status: {response.status_code}, Response: {response.text}")

# Lambda handler function
def lambda_handler(event, context):
    records = get_airtable_data()
    if records:
        for record in records:
            fields = record['fields']
            first_name = fields.get('First Name')
            last_name = fields.get('Last Name')
            email = fields.get('Email Address')
            phone_number = fields.get('Phone Number')
            email_template_id = fields.get('Template Selected', ['No Template'])[0]

            print(f"=======START for Customer {first_name}=======")
            print(f"email_template_id : {email_template_id}")
            if email_template_id:
                email_body = get_airtable_template(email_template_id)
                if email_body:
                    email_body = email_body.replace("[First Name]", first_name or "Partner")
                    if fields.get('Should Send Email') and email:
                        send_email_to_customer(first_name, email, email_body)

            whatsapp_campaign_name = fields.get('WhatsApp Template Selected', ['No Template'])[0]
            if whatsapp_campaign_name and fields.get('Should Send Whatsapp Message'):
                send_whatsapp_message(whatsapp_campaign_name, first_name, phone_number)

            print(f"=======END for Customer {first_name}=======")
    return {"statusCode": 200, "body": "Data processed successfully."}
