import requests
import time

API_URL = "http://localhost:8000/api/webhooks/sms"

print("📱 Simulating an incoming SMS from a victim without internet access...\n")

sms_payload = {
    "From": "+15550198472",
    "Body": "HELP! The bridge collapsed on Main Street. We have 3 injured people, we need a medical team immediately. It looks really bad!"
}

print(f"Incoming Text from {sms_payload['From']}:")
print(f"\"{sms_payload['Body']}\"\n")
print("Routing to IBM watsonx.ai for parsing...\n")

# Need to send as form-encoded data, which is how Twilio sends webhooks
response = requests.post(API_URL, data=sms_payload)

if response.status_code == 200:
    print("✅ SMS successfully processed and logged as a structured Field Report!")
    print("Response from server:", response.json())
    print("\nGo check the React Dashboard! You will see the new report automatically parsed by AI.")
else:
    print("❌ Failed to send SMS.")
    print(response.text)
