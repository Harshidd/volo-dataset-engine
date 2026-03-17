import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
LANGUAGES = ["en", "de", "nl", "es"]

def validate_dataset():
    all_ok = True
    print("🔍 Starting Dataset Validation...")
    
    for lang in LANGUAGES:
        file_path = DATA_DIR / f"{lang}.json"
        
        if not file_path.exists():
            print(f"❌ [ERROR] {lang}.json not found!")
            all_ok = False
            continue
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ [ERROR] Failed to parse {lang}.json: {e}")
            all_ok = False
            continue
            
        words = data.get("words", [])
        lang_name = data.get("language", "")
        
        errors = []
        
        # 1. Word count check
        if len(words) < 300:
            errors.append(f"Word count too low: {len(words)} (Min: 300)")
            
        # 2. Duplicate check
        word_list = [w.get("word") for w in words]
        duplicates = [w for w in set(word_list) if word_list.count(w) > 1]
        if duplicates:
            errors.append(f"Duplicate words found: {duplicates[:5]}...")
            
        # 3. Content check
        for i, entry in enumerate(words):
            word = entry.get("word", f"UnknownIndex_{i}")
            
            # Translation check
            if not entry.get("translation", {}).get("tr"):
                errors.append(f"Word '{word}': Missing translation.tr")
                
            # Contexts check
            contexts = entry.get("contexts", [])
            if len(contexts) < 2:
                errors.append(f"Word '{word}': Has {len(contexts)} contexts (Min: 2)")
                
            for ctx in contexts:
                ctx_name = ctx.get("name")
                if not ctx_name:
                    errors.append(f"Word '{word}': Empty context name")
                
                # Sentences check
                sentences = ctx.get("sentences", [])
                if not (3 <= len(sentences) <= 5):
                    errors.append(f"Word '{word}' context '{ctx_name}': Has {len(sentences)} sentences (Required: 3-5)")
                    
                for s in sentences:
                    if not s.get("base") or not s.get("translation"):
                        errors.append(f"Word '{word}' context '{ctx_name}': Missing base/translation in sentences")
                        
        if errors:
            print(f"❌ [ERROR] {lang}.json validation FAILED ({len(words)} words)")
            for err in errors[:10]: # Print first 10 errors
                print(f"  - {err}")
            if len(errors) > 10:
                print(f"  - ... and {len(errors) - 10} more errors.")
            all_ok = False
        else:
            print(f"✅ [OK] {lang}.json → {len(words)} words validated")

    if not all_ok:
        print("\n💥 CRITICAL: Dataset validation failed. Build stopped.")
        sys.exit(1)
    else:
        print("\n✨ All datasets are valid and production-ready.")

if __name__ == "__main__":
    validate_dataset()
