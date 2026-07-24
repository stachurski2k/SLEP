# Glossy <-> Text Translation

This module uses LLM models (defaulting to Google Gemini `gemini-2.5-flash`) to perform translation between standard English text and American Sign Language (ASL) glosses.

## Benchmarks (Ollama Llama 3.1)

- **Text ➔ Gloss**: BLEU: 55.02 | ROUGE-1: 91.05
- **Gloss ➔ Text**: BLEU: 82.21 | ROUGE-1: 96.55

*Tested on 45 sample pairs using local model.*

## Requirements

- Python 3.10+
- Google API Key (`GOOGLE_API_KEY`)

## Installation

You can install dependencies using a standard virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

*(If you use `uv`, you can run `uv sync` or `uv pip install -r requirements.txt`)*

Next, create a `.env` file in this folder (`txt-glossy`) and add your API key:
```env
GOOGLE_API_KEY=your_api_key_here
```

## Running the Web UI

To start the beautiful Web Interface (UI) using FastAPI:
```bash
uv run uvicorn api:app --reload
```
Then open `http://127.0.0.1:8000` in your web browser.


## Customization

Translation rules and system prompts for the LLM can be adjusted in the `translator.py` file.
