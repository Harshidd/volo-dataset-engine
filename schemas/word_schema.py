from pydantic import BaseModel, Field
from typing import List, Dict

class Sentence(BaseModel):
    base: str
    translation: str

class Context(BaseModel):
    name: str
    sentences: List[Sentence]

class WordEntry(BaseModel):
    word: str
    translation: Dict[str, str] = Field(..., description="Translations, e.g. {'tr': 'elma'}")
    contexts: List[Context]

class LanguageData(BaseModel):
    language: str
    words: List[WordEntry]
