import json
from pathlib import Path

data_dir = Path("data")
for file in data_dir.glob("*.json"):
    print(f"Loading {file.name}...")
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"✅ Success: {data.get('language')}")
    except Exception as e:
        print(f"❌ Failed: {e}")
