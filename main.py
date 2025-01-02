from flask import Flask, render_template, request
import openpyxl
import requests
from io import BytesIO

app = Flask(__name__)

@app.route('/')
def home():
    return '''
        <h1>Run Email Sender</h1>
        <form method="POST" action="/run">
            <button type="submit">Run Script</button>
        </form>
    '''

@app.route('/run', methods=['POST'])
def run_script():
    file_url = "https://example.com/path-to-excel.xlsx"  # Replace with your file URL
    local_file_path = "updated_customer_data.xlsx"  # Path to save updated file

    try:
        # Download the file
        response = requests.get(file_url)
        if response.status_code == 200:
            file_content = BytesIO(response.content)
            workbook = openpyxl.load_workbook(file_content)
            sheet = workbook.active

            # Process the file and update the "Status" column
            for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=False), start=2):
                name_cell, email_cell, status_cell = row[0], row[1], row[2]
                name = name_cell.value
                email = email_cell.value
                status = status_cell.value

                if status.lower() == "active":
                    send_status = send_email(email, name)
                    if send_status:
                        status_cell.value = "Email Sent"  # Update status in Excel
                    else:
                        status_cell.value = "Failed"  # Update status in Excel

            # Save the updated workbook locally
            workbook.save(local_file_path)

            return f"Emails processed! Updated file saved at {local_file_path}."
        else:
            return f"Failed to download the file. Status code: {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

def send_email(to_address, name):
    url = "https://api.zeptomail.in/v1.1/email"
    payload = {
        "from": {"address": "securebot@weqtechnologies.com", "name": "WEQ Technologies"},
        "to": [{"email_address": {"address": to_address, "name": name}}],
        "subject": "Greetings from WEQ Technologies",
        "htmlbody": f"<div><b>Hi {name},</b><br>We appreciate your interest in our services. Please feel free to reach out for any assistance!</div>",
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": "<SEND_MAIL_TOKEN>",  # Replace with your ZeptoMail token
    }
    response = requests.post(url, json=payload, headers=headers)
    print(f"Email to {name} ({to_address}) - Status: {response.status_code}")
    return response.status_code == 200  # Return True if email was sent successfully

if __name__ == '__main__':
    app.run(debug=True)
