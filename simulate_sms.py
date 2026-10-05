import requests
import time

API_URL = "http://localhost:8000/api/webhooks/sms"

print("Simulating an incoming SMS from a victim without internet access...\n")

sms_payload = {
    "From": "+15550198472",
    "Body": "¡AYUDA! El puente colapsó en la calle principal. Tenemos 3 personas heridas, necesitamos un equipo médico de inmediato. ¡Se ve muy mal!"
}

print(f"Incoming Text from {sms_payload['From']}:")
print(f"\"{sms_payload['Body']}\"\n")
print("Routing to IBM watsonx.ai for parsing...\n")

# Need to send as form-encoded data, which is how Twilio sends webhooks
response = requests.post(API_URL, data=sms_payload)

if response.status_code == 200:
    print("SMS successfully processed and logged as a structured Field Report!")
    print("Response from server:", response.json())
    print("\nGo check the React Dashboard! You will see the new report automatically parsed by AI.")
else:
    print("Failed to send SMS.")
    print(response.text)
