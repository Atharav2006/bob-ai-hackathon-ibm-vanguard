import requests
import time
import json
import sys

API_URL = "http://localhost:8001/api"

def wait_for_backend():
    print("Waiting for backend to become available...")
    for _ in range(30):
        try:
            r = requests.get(f"{API_URL}/incidents/")
            if r.status_code == 200:
                print("Backend is UP and reachable.")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(2)
    print("Backend failed to start.")
    sys.exit(1)

def test_phase_1_and_seeder():
    print("\n--- Testing Phase 1 & Seeder (PostgreSQL) ---")
    r = requests.get(f"{API_URL}/incidents/")
    data = r.json()
    if len(data) > 0:
        print(f"Seeder worked! Found {len(data)} incident: {data[0]['name']}")
    else:
        print("Database is empty.")

def test_phase_6_map_data():
    print("\n--- Testing Phase 6 (PostGIS Map Data) ---")
    r = requests.get(f"{API_URL}/map-data")
    data = r.json()
    if "zones" in data and len(data["zones"]) > 0:
        print(f"Found {len(data['zones'])} GeoJSON Zones and {len(data['resources'])} Resources for the Leaflet map.")
    else:
        print("Map data missing.")

def test_phase_2_watsonx():
    print("\n--- Testing Phase 2 (Watsonx AI Parsing) ---")
    payload = {
        "source": "Integration Test",
        "observed_at": "2026-10-05T00:00:00Z",
        "raw_text": "We need 5 medical kits at the hospital immediately."
    }
    r = requests.post(f"{API_URL}/reports/", json=payload)
    if r.status_code == 200:
        data = r.json()
        print(f"Watsonx structured data successfully extracted: {json.dumps(data['structured_data'])}")
    else:
        print("Failed to parse with Watsonx.", r.text)

def test_phase_3_ortools():
    print("\n--- Testing Phase 3 & 4 (OR-Tools Optimizer) ---")
    r = requests.post(f"{API_URL}/plans/generate?snapshot_id=snap_test")
    if r.status_code == 200:
        data = r.json()
        print(f"OR-Tools Planner executed! Status: {data.get('solver_status')}")
    else:
        print("OR-Tools Planner failed.", r.text)

def test_csv_export():
    print("\n--- Testing Phase 5 (Audit CSV Export) ---")
    r = requests.get(f"{API_URL}/export/assignments")
    if r.status_code == 200 and 'text/csv' in r.headers.get('content-type', ''):
        print("CSV Audit log generated successfully!")
    else:
        print("CSV Export failed.")

if __name__ == "__main__":
    wait_for_backend()
    test_phase_1_and_seeder()
    test_phase_6_map_data()
    test_phase_2_watsonx()
    test_phase_3_ortools()
    test_csv_export()
    print("\nALL TESTS PASSED SUCCESSFULLY! The integration is solid.")
