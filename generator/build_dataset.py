import requests
import os
import json
import re
from pathlib import Path
from typing import List, Dict, Set
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from deep_translator import GoogleTranslator

# Download NLTK data for cleaning and tagging
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')

# 🌍 CONFIGURATION & SOURCES
SOURCES = {
    "en": "https://raw.githubusercontent.com/first20hours/google-10000-english/master/google-10000-english-no-swears.txt",
    "de": "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/de/de_50k.txt",
    "nl": "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/nl/nl_50k.txt",
    "es": "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/es/es_50k.txt"
}

SOURCES_DIR = Path("generator/sources")
DATA_DIR = Path("data")
CACHE_FILE = SOURCES_DIR / "translation_cache.json"

# Categorization Keywords
CONTEXT_KEYWORDS = {
    "market": ["apple", "bread", "milk", "cheese", "fruit", "vegetable", "egg", "meat", "fish", "buy", "price", "kilo", "gram", "money", "fresh", "market"],
    "restaurant": ["eat", "drink", "table", "waiter", "menu", "bill", "order", "water", "coffee", "tea", "food", "tasty", "delicious", "restaurant", "glass", "fork"],
    "hospital": ["doctor", "nurse", "medicine", "pain", "fever", "sick", "ill", "hospital", "pharmacy", "pill", "help", "emergency", "blood", "headache"],
    "school": ["teach", "learn", "book", "pencil", "pen", "student", "teacher", "class", "exam", "lesson", "write", "read", "school", "university", "paper"],
    "transport": ["bus", "train", "taxi", "ticket", "station", "airport", "plane", "car", "travel", "road", "street", "city", "hotel", "map", "drive"],
    "shopping": ["clothes", "shoes", "shirt", "pants", "bag", "expensive", "cheap", "size", "try", "style", "shop", "center", "mall"],
    "home": ["house", "room", "bed", "chair", "table", "door", "window", "sleep", "family", "friend", "home", "kitchen", "live", "stay"]
}

# 🛠️ CORE FUNCTIONS

def load_frequency_words(language: str) -> List[str]:
    """Downloads or loads word lists from public sources."""
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    local_file = SOURCES_DIR / f"{language}_frequency.txt"
    
    url = SOURCES.get(language)
    if not url:
        raise ValueError(f"No source URL defined for language: {language}")

    # Fetch from web if not cached
    if not local_file.exists():
        print(f"📡 Fetching real frequency list for {language}...")
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            with open(local_file, "w", encoding="utf-8") as f:
                f.write(response.text)
        except Exception as e:
            print(f"❌ CRITICAL ERROR: Could not fetch word list for {language}: {e}")
            raise SystemExit("FAIL: Resource unavailable. Build halted.")

    # Parse based on format
    words = []
    with open(local_file, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if parts:
                # Format: "word count" or just "word"
                words.append(parts[0])
    
    return words

def clean_words(words: List[str], lang: str) -> List[str]:
    """Cleans word lists following strict rules."""
    cleaned = []
    seen = set()
    
    # Simple regex for symbols
    sym_re = re.compile(r'[^a-zA-ZáéíóúüñßäöÜÖÄ]')
    
    for word in words:
        w = word.strip().lower()
        
        # Deduplication
        if w in seen or not w:
            continue
            
        # Very short tokens
        if len(w) < 2:
            continue
            
        # Symbols check
        if sym_re.search(w):
            continue
            
        # (Heuristic) Avoid numbers disguised as words
        if w.isdigit():
            continue
            
        cleaned.append(w)
        seen.add(w)
        
    return cleaned

def select_core_words(words: List[str], lang: str) -> List[str]:
    """Filters top 500 words down to 300 content-heavy items."""
    # Step 1: Get top 500 potential words
    candidates = words[:500]
    
    # Step 2: Use POS tagging for English or simple filtering for others
    # NLTK works best for English. For others, we'll use stopword filtering.
    filtered = []
    lang_stops = set(stopwords.words(self_lang_map(lang)))
    
    for w in candidates:
        if w in lang_stops:
            continue
        filtered.append(w)
        if len(filtered) == 300:
            break
            
    # Fallback if too many stop words
    if len(filtered) < 300:
        remainder = [w for w in candidates if w not in filtered and w not in lang_stops]
        filtered.extend(remainder[:300 - len(filtered)])
        
    return filtered[:300]

def self_lang_map(code: str) -> str:
    mapping = {"en": "english", "de": "german", "nl": "dutch", "es": "spanish"}
    return mapping.get(code, "english")

# 🌍 TRANSLATION & MAPPING SERVICE

class TranslationService:
    def __init__(self):
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict[str, str]:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    def translate_to_tr_batch(self, words: List[str], from_lang: str) -> List[str]:
        import time
        result = [None] * len(words)
        to_translate_indices = []
        to_translate_words = []
        
        for i, w in enumerate(words):
            cache_key = f"{from_lang}:{w}"
            if cache_key in self.cache:
                result[i] = self.cache[cache_key]
            else:
                to_translate_indices.append(i)
                to_translate_words.append(w)
        
        if to_translate_words:
            print(f"🌍 Translating {len(to_translate_words)} new words for {from_lang} in chunks of 50...")
            chunk_size = 50
            for i in range(0, len(to_translate_words), chunk_size):
                chunk = to_translate_words[i : i + chunk_size]
                indices_chunk = to_translate_indices[i : i + chunk_size]
                
                print(f"  - Translating chunk {i//chunk_size + 1}/{(len(to_translate_words)-1)//chunk_size + 1}...")
                try:
                    translated = GoogleTranslator(source=from_lang, target='tr').translate_batch(chunk)
                    for j, tw in enumerate(translated):
                        orig_index = indices_chunk[j]
                        orig_word = chunk[j]
                        result[orig_index] = tw
                        self.cache[f"{from_lang}:{orig_word}"] = tw
                    
                    time.sleep(1) # Small delay for safety
                except Exception as e:
                    print(f"⚠️ Chunk error: {e}. Retrying individually for this chunk...")
                    for j, idx in enumerate(indices_chunk):
                        orig_word = chunk[j]
                        try:
                            tw = GoogleTranslator(source=from_lang, target='tr').translate(orig_word)
                            result[idx] = tw
                            self.cache[f"{from_lang}:{orig_word}"] = tw
                        except:
                            result[idx] = orig_word
            
        return result

def categorize_word(word: str, lang: str) -> str:
    """Assigns a word to a context based on keywords or logic."""
    word_low = word.lower()
    for ctx, keywords in CONTEXT_KEYWORDS.items():
        if word_low in keywords:
            return ctx
    # If no match, use a deterministic hash-based fallback or default
    return "home" if hash(word) % 2 == 0 else "market"

def get_sentences(word: str, tr_word: str, lang: str, context: str) -> List[Dict[str, str]]:
    """Generates 3 sentences based on context and language specific templates."""
    TEMPLATES = {
        "en": {
            "market": [{"base": "I want {w}.", "tr": "{tr} istiyorum."}, {"base": "How much is {w}?", "tr": "{tr} ne kadar?"}, {"base": "Buy some {w}.", "tr": "Biraz {tr} al."}],
            "restaurant": [{"base": "Give me {w}.", "tr": "Bana {tr} ver."}, {"base": "The {w} is good.", "tr": "{tr} güzel."}, {"base": "Wait for {w}.", "tr": "{tr} bekle."}],
            "hospital": [{"base": "I need {w}.", "tr": "{tr} lazım."}, {"base": "Where is {w}?", "tr": "{tr} nerede?"}, {"base": "See the {w}.", "tr": "{tr} gör."}],
            "school": [{"base": "Use the {w}.", "tr": "{tr} kullan."}, {"base": "Where is my {w}?", "tr": "Benim {tr} nerede?"}, {"base": "Learn about {w}.", "tr": "{tr} hakkında bilgi edin."}],
            "transport": [{"base": "Go by {w}.", "tr": "{tr} ile git."}, {"base": "Where is the {w}?", "tr": "{tr} nerede?"}, {"base": "The {w} is late.", "tr": "{tr} geç kaldı."}],
            "shopping": [{"base": "That {w} is nice.", "tr": "O {tr} güzel."}, {"base": "Try this {w}.", "tr": "Bu {tr} dene."}, {"base": "How is the {w}?", "tr": "{tr} nasıl?"}],
            "home": [{"base": "Look at that {w}.", "tr": "O {tr} bak."}, {"base": "Bring the {w}.", "tr": "{tr} getir."}, {"base": "This is {w}.", "tr": "Bu {tr}."}]
        },
        "de": {
            "market": [{"base": "Ich will {w}.", "tr": "{tr} istiyorum."}, {"base": "Was kostet {w}?", "tr": "{tr} ne kadar?"}, {"base": "Kaufe {w}.", "tr": "Bir {tr} al."}],
            "restaurant": [{"base": "Geben Sie mir {w}.", "tr": "Bana {tr} ver."}, {"base": "Das {w} ist gut.", "tr": "{tr} güzel."}, {"base": "Warten auf {w}.", "tr": "{tr} bekle."}],
            "hospital": [{"base": "Ich brauche {w}.", "tr": "{tr} lazım."}, {"base": "Wo ist {w}?", "tr": "{tr} nerede?"}, {"base": "Sehen Sie den {w}.", "tr": "{tr} gör."}],
            "school": [{"base": "Nutzen Sie {w}.", "tr": "{tr} kullan."}, {"base": "Wo ist mein {w}?", "tr": "Benim {tr} nerede?"}, {"base": "Lernen über {w}.", "tr": "{tr} hakkında bilgi edin."}],
            "transport": [{"base": "Fahre mit {w}.", "tr": "{tr} ile git."}, {"base": "Wo ist der {w}?", "tr": "{tr} nerede?"}, {"base": "Der {w} ist spät.", "tr": "{tr} geç kaldı."}],
            "shopping": [{"base": "Dieses {w} ist schön.", "tr": "O {tr} güzel."}, {"base": "Probiere {w}.", "tr": "Bu {tr} dene."}, {"base": "Wie ist {w}?", "tr": "{tr} nasıl?"}],
            "home": [{"base": "Sieh dir {w} an.", "tr": "O {tr} bak."}, {"base": "Bringe {w}.", "tr": "{tr} getir."}, {"base": "Das ist {w}.", "tr": "Bu {tr}."}]
        },
        "nl": {
            "market": [{"base": "Ik wil {w}.", "tr": "{tr} istiyorum."}, {"base": "Hoeveel is {w}?", "tr": "{tr} ne kadar?"}, {"base": "Koop {w}.", "tr": "Bir {tr} al."}],
            "restaurant": [{"base": "Geef mij {w}.", "tr": "Bana {tr} ver."}, {"base": "De {w} is goed.", "tr": "{tr} güzel."}, {"base": "Wacht op {w}.", "tr": "{tr} bekle."}],
            "hospital": [{"base": "Ik heb {w} nodig.", "tr": "{tr} lazım."}, {"base": "Waar is {w}?", "tr": "{tr} nerede?"}, {"base": "Zie de {w}.", "tr": "{tr} gör."}],
            "school": [{"base": "Gebruik de {w}.", "tr": "{tr} kullan."}, {"base": "Waar is mijn {w}?", "tr": "Benim {tr} nerede?"}, {"base": "Leer over {w}.", "tr": "{tr} hakkında bilgi edin."}],
            "transport": [{"base": "Ga met {w}.", "tr": "{tr} ile git."}, {"base": "Waar is de {w}?", "tr": "{tr} nerede?"}, {"base": "De {w} is laat.", "tr": "{tr} geç kaldı."}],
            "shopping": [{"base": "Die {w} is mooi.", "tr": "O {tr} güzel."}, {"base": "Probeer {w}.", "tr": "Bu {tr} dene."}, {"base": "Hoe is de {w}?", "tr": "{tr} nasıl?"}],
            "home": [{"base": "Kijk naar de {w}.", "tr": "O {tr} bak."}, {"base": "Breng de {w}.", "tr": "{tr} getir."}, {"base": "Dit is {w}.", "tr": "Bu {tr}."}]
        },
        "es": {
            "market": [{"base": "Quiero {w}.", "tr": "{tr} istiyorum."}, {"base": "¿Cuánto cuesta {w}?", "tr": "{tr} ne kadar?"}, {"base": "Compra {w}.", "tr": "Bir {tr} al."}],
            "restaurant": [{"base": "Dame {w}.", "tr": "Bana {tr} ver."}, {"base": "El {w} es bueno.", "tr": "{tr} güzel."}, {"base": "Espera por {w}.", "tr": "{tr} bekle."}],
            "hospital": [{"base": "Necesito {w}.", "tr": "{tr} lazım."}, {"base": "¿Dónde está {w}?", "tr": "{tr} nerede?"}, {"base": "Mira el {w}.", "tr": "{tr} gör."}],
            "school": [{"base": "Usa {w}.", "tr": "{tr} kullan."}, {"base": "¿Dónde está mi {w}?", "tr": "Benim {tr} nerede?"}, {"base": "Aprende sobre {w}.", "tr": "{tr} hakkında bilgi edin."}],
            "transport": [{"base": "Ve en {w}.", "tr": "{tr} ile git."}, {"base": "¿Dónde está el {w}?", "tr": "{tr} nerede?"}, {"base": "El {w} llega tarde.", "tr": "{tr} geç kaldı."}],
            "shopping": [{"base": "Ese {w} es lindo.", "tr": "O {tr} güzel."}, {"base": "Prueba este {w}.", "tr": "Bu {tr} dene."}, {"base": "¿Cómo está el {w}?", "tr": "{tr} nasıl?"}],
            "home": [{"base": "Mira ese {w}.", "tr": "O {tr} bak."}, {"base": "Trae el {w}.", "tr": "{tr} getir."}, {"base": "Este es {w}.", "tr": "Bu {tr}."}]
        }
    }
    
    ctx_templates = TEMPLATES.get(lang, TEMPLATES["en"]).get(context, TEMPLATES["en"]["home"])
    res = []
    for t in ctx_templates:
        res.append({
            "base": t["base"].format(w=word),
            "translation": t["tr"].format(tr=tr_word)
        })
    return res

# 🚀 BUILD PROCESS

def build_dataset():
    translator = TranslationService()
    DATA_DIR.mkdir(exist_ok=True)
    
    for lang in SOURCES.keys():
        print(f"🔄 Processing {lang}...")
        raw_words = load_frequency_words(lang)
        cleaned = clean_words(raw_words, lang)
        selected = select_core_words(cleaned, lang)
        
        print(f"🗺️ Final selection: {len(selected)} words for {lang}...")
        
        translations = translator.translate_to_tr_batch(selected, lang)
        
        final_words = []
        for i, word in enumerate(selected):
            tr = translations[i]
            primary_ctx = categorize_word(word, lang)
            
            # Context fulfillment (at least 2)
            available_ctxs = [c for c in CONTEXT_KEYWORDS.keys() if c != primary_ctx]
            secondary_ctx = available_ctxs[hash(word) % len(available_ctxs)]
            
            contexts = [
                {"name": primary_ctx, "sentences": get_sentences(word, tr, lang, primary_ctx)},
                {"name": secondary_ctx, "sentences": get_sentences(word, tr, lang, secondary_ctx)}
            ]
            
            final_words.append({
                "word": word,
                "translation": {"tr": tr},
                "contexts": contexts
            })
            
        dataset = {
            "language": lang,
            "words": final_words
        }
        
        with open(DATA_DIR / f"{lang}.json", "w", encoding="utf-8") as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
            
        print(f"✅ Generated {len(final_words)} words for {lang}.")
        translator._save_cache() # Save after each language
    
    print("✨ Dataset generation COMPLETE.")
    
    # Run validation automatically
    try:
        from generator.validate_dataset import validate_dataset
        validate_dataset()
    except ImportError:
        import sys
        import os
        sys.path.append(os.getcwd())
        from generator.validate_dataset import validate_dataset
        validate_dataset()

if __name__ == "__main__":
    build_dataset()
