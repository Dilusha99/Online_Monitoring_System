import requests
import random
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Retry-enabled session
session = requests.Session()
retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

URL = "http://127.0.0.1:5000/data"
#URL = "https://ineffaceably-unguarded-evelina.ngrok-free.dev/data"
PLANT_NAMES = {
    1: "pta", 2: "bgd", 3: "tha", 4: "klp", 5: "gru",
    6: "ww1", 7: "ww2", 8: "gam", 9: "weg", 10: "fav",
    11: "bc1", 12: "bc2", 13: "nak"
}

PLANT_CONFIG = {
    1: 1, 2: 2, 3: 2, 4: 2, 5: 3, 6: 2,
    7: 2, 8: 2, 9: 3, 10: 2, 11: 1, 12: 2, 13: 2
}

def send_data(data, attempt=1, max_attempts=3):
    try:
        response = session.post(URL, json=data, headers={'Content-Type': 'application/json'}, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if attempt < max_attempts:
            time.sleep(attempt)
            return send_data(data, attempt + 1, max_attempts)
        else:
            return {"status": "error", "message": str(e)}

def generate_esp32_json(plant_name, unit_id):
    """Generate ESP32-style JSON for one unit without calculating power"""
    return {
        f"{plant_name}_u{unit_id}_power": random.randint(1000, 2000),
        f"{plant_name}_u{unit_id}_current_L1": random.randint(100, 200),
        f"{plant_name}_u{unit_id}_current_L2": random.randint(100, 200),
        f"{plant_name}_u{unit_id}_current_L3": random.randint(100, 200),
        f"{plant_name}_u{unit_id}_voltage_L12": random.randint(100, 230),
        f"{plant_name}_u{unit_id}_voltage_L23": random.randint(100, 230),
        f"{plant_name}_u{unit_id}_voltage_L13": random.randint(100, 230),
        f"{plant_name}_u{unit_id}_energy": random.randint(1000000, 2000000),
        f"{plant_name}_u{unit_id}_runtime": random.randint(1000, 100000)
    }

def main():
    sample_count = 0
    try:
        while True:
            for plant_id, unit_count in PLANT_CONFIG.items():
                plant_name = PLANT_NAMES[plant_id]

                for unit_id in range(1, unit_count + 1):
                    data = generate_esp32_json(plant_name, unit_id)
                    sample_count += 1

                    print(f"\n📊 Sample #{sample_count}")
                    print(f"🏭 Plant {plant_id} | Unit {unit_id}")
                    print(f"📦 JSON: {data}")

                    response = send_data(data)
                    if response.get("status") == "success":
                        print(f"✅ Stored successfully")
                    else:
                        print(f"❌ Error: {response.get('message', 'Unknown error')}")

                    time.sleep(0.1)

            print("\n⏰ Cycle complete. Next cycle in 5s...")
            time.sleep(5)

    except KeyboardInterrupt:
        print(f"\n🛑 Simulation stopped by user")
        print(f"📊 Total samples sent: {sample_count}")

if __name__ == "__main__":
    main()
