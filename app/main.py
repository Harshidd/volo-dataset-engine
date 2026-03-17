from fastapi import FastAPI, Query, HTTPException
from typing import List, Optional
from app.services.data_service import data_service

app = FastAPI(title="VOLO Dataset Engine API")

@app.get("/")
def read_root():
    return {"status": "online", "message": "VOLO Dataset Engine API is running. Try /languages to see available data."}

@app.get("/languages")
def get_languages():
    return {"languages": data_service.get_languages()}

@app.get("/contexts")
def get_contexts():
    return {"contexts": data_service.get_contexts()}

@app.get("/words")
def get_words(
    lang: str = Query(..., description="Language code (en, de, nl, es)"),
    limit: int = Query(10, ge=1, le=100)
):
    words = data_service.get_words(lang, limit)
    if not words:
        raise HTTPException(status_code=404, detail=f"Language '{lang}' not found or no data available.")
    return {"language": lang, "count": len(words), "words": words}

@app.get("/practice")
def get_practice(
    lang: str = Query(..., description="Language code"),
    context: str = Query(..., description="Context name (market, restaurant, etc.)")
):
    practice_data = data_service.get_practice(lang, context)
    if not practice_data["data"]:
        raise HTTPException(status_code=404, detail=f"No data found for language '{lang}' in context '{context}'.")
    return practice_data

@app.get("/word/{word}")
def get_word(word: str):
    detail = data_service.get_word_detail(word)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Word '{word}' not found in any language dataset.")
    return detail

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)