# volo-dataset-engine 🌍

A production-ready dataset engine and API for language learning apps. It generates deterministic, context-mapped language data across multiple languages and serves them via a fast, AI-free API.

## 🎯 Architecture

This project is built with three distinct layers:

1.  **Dataset Generator (Offline)**: A Python script that transforms curated word sources and deterministic templates into high-quality JSON datasets.
2.  **Data Schema (Strict)**: Uses Pydantic to ensure all word entries follow a predefined, deep structure with multiple contexts and practical sentences.
3.  **API Layer (FastAPI)**: A high-performance serving layer that loads pre-generated data from disk. No AI calls at runtime. No request-time data generation.

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.11+
- Virtual environment (recommended)

### 2. Installation
```bash
pip install -r requirements.txt
```

### 3. Generate the Dataset
Before starting the API, you MUST generate the latest datasets:
```bash
python generator/build_dataset.py
```
This will populate the `/data` directory with `en.json`, `de.json`, `nl.json`, and `es.json`.

### 4. Run the API
```bash
uvicorn app.main:app --reload
```
The API documentation will be available at: [http://localhost:8000/docs](http://localhost:8000/docs)

## 📡 API Endpoints

- **GET /languages**: Returns available codes (en, de, nl, es).
- **GET /words?lang=en&limit=10**: Returns a set of pre-generated words for the requested language.
- **GET /practice?lang=en&context=market**: Returns words and sentences grouped by context (market, restaurant, etc.).
- **GET /word/{word}**: Returns full details (translations, sentences in all contexts) for a specific word.

## 🧠 Data Design Principles

- **Deterministic**: Every run of the generator produces identical results for a given source.
- **Practicality**: Sentences are curated for real-life usage (hospital, transport, restaurant).
- **No Randomness at Runtime**: The API serves pre-calculated data only.
- **Strict Validation**: Pydantic schemas enforce at least 2 contexts per word and 3 sentences per context.

## 🌍 Supported Languages
- English (en)
- German (de)
- Dutch (nl) - Belgian variants prioritized
- Spanish (es)
- Turkish (tr) - Translation target
