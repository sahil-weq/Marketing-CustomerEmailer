import requests
import json
import html
import re

# Airtable API credentials and URL
API_KEY = 'patqi7T4XLXXxUs2i.eba91528e22c97230f1833a1b4bd605f8e02cf47092b89e1018c388634828647'  # Replace with your Airtable API key
BASE_ID = 'appy8Yts8O6ZV2rks'  # Your Airtable Base ID
AISENSY_API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY2YTc5ZmZiOWY4MWJmMGI3NzhjZWUxZCIsIm5hbWUiOiJXRVEgVGVjaG5vbG9naWVzIiwiYXBwTmFtZSI6IkFpU2Vuc3kiLCJjbGllbnRJZCI6IjY2YTc5ZmZiOWY4MWJmMGI3NzhjZWUwZSIsImFjdGl2ZVBsYW4iOiJCQVNJQ19NT05USExZIiwiaWF0IjoxNzIyMjYxNDk5fQ.8suQQc0pO-vT0N6C9KUpccM0-L4GaC9ilZ2-sSQOlZY' # API key for WhatsApp authentication.

# Headers with API Key for Authorization
headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

# Function to get records from Airtable with pagination
def get_airtable_data():
    TABLE_NAME = 'Customers'  # Your Airtable Table name
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}'
    params = {
        "maxRecords": 10,  # Set the number of records to fetch per request
        "view": "Grid view"  # Replace with your view name if needed
    }
    all_records = []

    while True:
        # Make a GET request to fetch the records from Airtable
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            records = data['records']
            all_records.extend(records)

            # Check if there is a next page
            if 'offset' in data:
                params['offset'] = data['offset']  # Update the offset for the next request
            else:
                break  # Exit the loop if no more pages
        else:
            print(f"Error: {response.status_code}, Message: {response.text}")
            break  # Exit the loop if there's an error

    return all_records

# Fucntion to get records from Airtable with Template data
def get_airtable_template(template_id):
    TABLE_NAME = 'Templates'  # Your Airtable Table name
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}/{template_id}'

    response = requests.get(url, headers=headers)
    # print(json.dumps(response.json(),indent=4))

    response_data = response.json()

    if response_data:
        return response_data.get("fields", {}).get("Email Body", "")
    else:
        print(f"Template '{template_id}' not found.")
        return None

# Fucntion to get records from Airtable with Template data for Whatsapp
def get_airtable_template_whatsapp(template_id):
    TABLE_NAME = 'Templates'  # Your Airtable Table name
    url = f'https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}/{template_id}'

    response = requests.get(url, headers=headers)
    # print(json.dumps(response.json(),indent=4))

    response_data = response.json()

    if response_data:
        return response_data.get("fields", {}).get("Template Name", "")
    else:
        print(f"WhatsApp Template '{template_id}' not found.")
        return None


# Function to convert the message to HTML format for email template
def convert_to_html(text):
    # Escape any special HTML characters in the text
    escaped_text = html.escape(text)

    # Replace newlines with <br> tags to preserve formatting
    html_formatted = escaped_text.replace("\n", "<br>")

    # Wrap the content in basic HTML structure
    html_content = f"""
    <html>
        <body>
            <div style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6;">
                {html_formatted}
            </div>
        </body>
    </html>
    """
    return html_content

# Function to send emails (using Zepto Mail or any other service)
def send_email_to_customer(first_name, email, email_template):
    # Example of sending the email using Zepto Mail (as per your earlier code)
    email_html = convert_to_html(email_template)
    payload = {
        "from": { "address": "noreply@weqtech.com" },
        "to": [{"email_address": {"address": email, "name": first_name}}],
        "subject": "Your Custom Email",
        "htmlbody": email_html
    }
    response = requests.post(
        "https://api.zeptomail.in/v1.1/email",
        headers={
            'Authorization': 'Zoho-enczapikey PHtE6r0ME7zrg2N9oEVW5aDqQs+hZ4kr9OIzKgdOsN1LXqRSH01TqYwvkjS0/R95XPgXHKHIm4s+s7qYt7iFdG7kNjofXWqyqK3sx/VYSPOZsbq6x00etlsackHdUoDqcdJo1CzRu93YNA==',
            'Content-Type': 'application/json'
        },
        data=json.dumps(payload)
    )
    
    if response.status_code == 200:
        print(f"Email sent to {email}")
    else:
        print(f"Error: {response.status_code}, Message: {response.text}")

# Function to check the 10 digit India Format
def validate_and_format_phone(phone_number):
    """
    Validates and formats the phone number to ensure it includes the +91 country code for Indian numbers.
    Args:
        phone_number (str): The phone number to validate and format.
    Returns:
        str or None: The formatted phone number with +91 or None if invalid.
    """
    # Check if the number already starts with "91" and is 12 digits long
    if re.fullmatch(r"91\d{10}", phone_number):
        return f"+{phone_number}"  # Add + if not present
    # Check if it's a 10-digit number
    elif re.fullmatch(r"\d{10}", phone_number):
        return f"+91{phone_number}"  # Add +91 for 10-digit numbers
    else:
        print(f"Invalid phone number: {phone_number}")
        return None


# Function to send WhatsApp notification to Customers
def send_whatsapp_message(campaign_name, first_name, phone_number):
    """
    Sends a WhatsApp message to the customer using AISensy API.
    """

    url = "https://backend.aisensy.com/campaign/t1/api/v2"
    
    # Validate and format phone number
    destination = validate_and_format_phone(phone_number)

    if not phone_number or not first_name or not destination:
        return "Missing required details for customer"

    # Customize template parameters or attributes
    template_params = [first_name]


    # Define payload
    payload = {
        "apiKey": AISENSY_API_KEY,
        "campaignName": campaign_name,
        "destination": destination,
        "userName": first_name,
        "source": "Python Script",
        "templateParams": template_params,
    }

    headers = {
        "Content-Type": "application/json"
    }

    # Send POST request
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        print(f"WhatsApp message sent successfully to {first_name} ({phone_number})")
    else:
        print(f"Failed to send WhatsApp message. Status: {response.status_code}, Response: {response.text}")


# Main function to process Airtable data
def process_airtable_data():
    records = get_airtable_data()

    if records:
        for record in records:
            fields = record['fields']
            first_name = fields.get('First Name')
            last_name = fields.get('Last Name')
            company_name = fields.get('Company Name')
            email = fields.get('Email Address')
            phone_number = fields.get('Phone Number')
            status = fields.get('Status')
            should_send_email = fields.get('Should Send Email', False)
            should_send_whatsapp = fields.get('Should Send Whatsapp Message', False)
            email_template = fields.get('Template Selected', ['No Template'])
            whatsapp_template = fields.get('WhatsApp Template Selected', ['No Template'])

            print(f"============= Customer {first_name} START =============")
            # Fetch the email template
            # Fetch the email template safely
            email_body = get_airtable_template(next(iter(email_template), 'No Template'))

            # Fetch the whatsapp template safely
            whatsapp_campaign_name = get_airtable_template_whatsapp(next(iter(whatsapp_template), 'No Template'))

            if email_body:
                # Replace placeholders in the template
                email_body = email_body.replace("[First Name]", first_name or "Partner")
                email_body = email_body.replace("[Last Name]", last_name or "")
                email_body = email_body.replace("[Company Name]", company_name or "Your Firm")

                if should_send_email and email:
                    print(f"Processing Email for customer {first_name} with status {status}...")
                    send_email_to_customer(first_name, email, email_body)
                    
                    # Update the status in Airtable (if needed, for example, to "Email Sent")
                    # Here you can make a PUT or PATCH request to update the record status.

                    # Example: You could use the record ID to update the status:
                    # record_id = record['id']
                    # update_status(record_id, "Email Sent")
            
            if whatsapp_campaign_name and should_send_whatsapp:
                print(f"Processing WhatsApp for customer {first_name} with status {status}...")
                send_whatsapp_message(whatsapp_campaign_name, first_name, phone_number)
            
                # Update the status in Airtable (if needed, for example, to "Email Sent")
                # Here you can make a PUT or PATCH request to update the record status.

                # Example: You could use the record ID to update the status:
                # record_id = record['id']
                # update_status(record_id, "Email Sent")

            print(f"============= Customer {first_name} END =============")
            
    else:
        print("No data found in Airtable.")

# Function to update record status in Airtable
def update_status(record_id, status):
    update_url = f"{url}/{record_id}"
    data = {
        "fields": {
            "Status": status
        }
    }
    response = requests.patch(update_url, headers=headers, json=data)
    if response.status_code == 200:
        print(f"Status updated to '{status}' for record {record_id}")
    else:
        print(f"Error updating status: {response.status_code}, Message: {response.text}")

# Run the process
process_airtable_data()
