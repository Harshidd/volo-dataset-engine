import requests
import sys

BASE_URL = "http://localhost:8000"

def test_api():
    print("🚀 Starting API Validation Tests...")
    all_pass = True
    
    # 1. Test /languages
    try:
        r = requests.get(f"{BASE_URL}/languages")
        r.raise_for_status()
        langs = r.json().get("languages", [])
        if not langs:
            print("❌ [ERROR] /languages returned empty list")
            all_pass = False
        else:
            print(f"✅ [OK] /languages -> {langs}")
    except Exception as e:
        print(f"❌ [ERROR] /languages request failed: {e}")
        all_pass = False

    # 2. Test /words?lang=en
    try:
        r = requests.get(f"{BASE_URL}/words", params={"lang": "en", "limit": 5})
        r.raise_for_status()
        data = r.json()
        if len(data.get("words", [])) != 5:
            print(f"❌ [ERROR] /words?lang=en&limit=5 returned {len(data.get('words', []))} words")
            all_pass = False
        else:
            print("✅ [OK] /words?lang=en returns correct word count")
    except Exception as e:
        print(f"❌ [ERROR] /words?lang=en request failed: {e}")
        all_pass = False

    # 3. Test /word/{word}
    try:
        # Get a word first
        r_list = requests.get(f"{BASE_URL}/words", params={"lang": "en", "limit": 1})
        word_text = r_list.json()["words"][0]["word"]
        
        r = requests.get(f"{BASE_URL}/word/{word_text}")
        r.raise_for_status()
        word_data = r.json()
        if word_data.get("word").lower() != word_text.lower():
            print(f"❌ [ERROR] /word/{word_text} returned wrong word: {word_data.get('word')}")
            all_pass = False
        else:
            print(f"✅ [OK] /word/{word_text} returns correct detail")
    except Exception as e:
        print(f"❌ [ERROR] /word/ detail request failed: {e}")
        all_pass = False

    # 4. Test /practice?lang=en&context=market
    try:
        r = requests.get(f"{BASE_URL}/practice", params={"lang": "en", "context": "market"})
        r.raise_for_status()
        data = r.json()
        if not data.get("data"):
            print("❌ [ERROR] /practice?lang=en&context=market returned empty data")
            all_pass = False
        else:
            print("✅ [OK] /practice?lang=en&context=market returns valid scenarios")
    except Exception as e:
        print(f"❌ [ERROR] /practice request failed: {e}")
        all_pass = False

    if not all_pass:
        print("\n❌ API Validation FAILED.")
        sys.exit(1)
    else:
        print("\n✨ API Validation SUCCESSFUL. All endpoints operating correctly.")

if __name__ == "__main__":
    test_api()
