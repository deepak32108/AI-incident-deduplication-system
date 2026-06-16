import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000/api"

mock_incidents = [
    {
        "title": "Pressure Drop Alert - Sector 4 Pipeline",
        "description": "SCADA system triggered an automated alert: sudden pressure drop detected in Sector 4 transmission pipeline near the main valve assembly. Potential breach or seal failure.",
        "severity": "critical",
        "source": "SCADA_Telemetry"
    },
    {
        "title": "Thermal Overheat in Compression Station 2",
        "description": "Temperature readings on main compressor pump B exceeded safe operating thresholds, peaking at 115 degrees Celsius. Automated shutdown sequence initiated.",
        "severity": "high",
        "source": "Thermal_Sensors"
    },
    {
        "title": "Sector 4 Telemetry Pressure Loss",
        "description": "Automated logs indicate a rapid loss of operational pressure within the pipeline running through Sector 4 close to the main valve setup. Investigating flow fluctuations.",
        "severity": "critical",
        "source": "Field_Operator_App"
    },
    {
        "title": "Routine Sensor Calibration Due",
        "description": "Scheduled preventative maintenance reminder: Periodic verification and calibration required for methane gas detectors across the processing facility layout.",
        "severity": "low",
        "source": "Asset_Management_System"
    }
]

print("\n" + "=" * 60)
print("🚀 STARTING AI INCIDENT DEDUPLICATION SIMULATION")
print("=" * 60)

for idx, incident in enumerate(mock_incidents, start=1):
    print(f"[{idx}/4] Sending incident: '{incident['title']}'...")
    try:
        response = requests.post(f"{BASE_URL}/incidents", json=incident)
        if response.status_code == 201 or response.status_code == 200:
            res_data = response.json()
            if res_data.get("is_duplicate"):
                print(f"   ❌ AI INTERCEPTED DUPLICATE! (Match Score: {res_data.get('similarity_score')})")
                print(f"      Linked to Primary Incident ID: {res_data.get('duplicate_of')}")
            else:
                print(f"   ✅ UNIQUE INCIDENT CREATED. Saved cleanly to SQLite. (ID: {res_data.get('id')})")
        else:
            print(f"   ⚠️ Server rejected request with status {response.status_code}: {response.text}")
    except requests.exceptions.ConnectionError:
        print("   🚨 ERROR: Could not connect to the API server. Is your Flask application running?")
        break
    time.sleep(1)

print("\n" + "=" * 60)
print("📊 FETCHING DASHBOARD LIFECYCLE METRICS")
print("=" * 60)
try:
    stats_resp = requests.get(f"{BASE_URL}/incidents/stats")
    print(json.dumps(stats_resp.json(), indent=4))
except Exception as e:
    print(f"Failed to fetch stats: {e}")
