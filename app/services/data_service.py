import json
from pathlib import Path
from typing import List, Dict, Optional
import random

class DataService:
    def __init__(self):
        self.data_dir = Path("data")
        self.cache: Dict[str, dict] = {}
        self._load_all()

    def _load_all(self):
        for file in self.data_dir.glob("*.json"):
            lang = file.stem
            with open(file, "r", encoding="utf-8") as f:
                self.cache[lang] = json.load(f)

    def get_languages(self) -> List[str]:
        return list(self.cache.keys())

    def get_contexts(self) -> List[str]:
        return ["market", "restaurant", "hospital", "school", "transport", "shopping", "home"]

    def get_words(self, lang: str, limit: int = 10) -> List[dict]:
        if lang not in self.cache:
            return []
        
        words = self.cache[lang].get("words", [])
        # Deterministic "random" for production repeatability or just shuffle?
        # User said "Returns random but pre-generated words"
        # I'll use a local random seed for consistency if needed, but standard random is fine for "random words"
        return random.sample(words, min(len(words), limit))

    def get_practice(self, lang: str, context: str) -> dict:
        if lang not in self.cache:
            return {"context": context, "words": []}
        
        words = self.cache[lang].get("words", [])
        filtered_words = []
        
        for w in words:
            # Find the specific context in word's contexts
            matching_contexts = [c for c in w["contexts"] if c["name"] == context]
            if matching_contexts:
                # Group words + sentences for that context
                filtered_words.append({
                    "word": w["word"],
                    "translation": w["translation"],
                    "sentences": matching_contexts[0]["sentences"]
                })
        
        return {
            "context": context,
            "language": lang,
            "data": filtered_words
        }

    def get_word_detail(self, word_text: str) -> Optional[dict]:
        # Search across any language or specific? User said /word/{word}
        # Assuming it searches in all available languages and returns the first match or groups them?
        # Usually /word/{word} implies a specific lookup.
        # I'll search across all languages.
        for lang, data in self.cache.items():
            for w in data.get("words", []):
                if w["word"].lower() == word_text.lower():
                    return w
        return None

data_service = DataService()
