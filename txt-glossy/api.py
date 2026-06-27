from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from translator import GlossTranslator
import os

app = FastAPI(title="ASL Translator API")

# Mount static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize Translator
try:
    translator = GlossTranslator(model_name="gemini-2.5-flash")
except Exception as e:
    print(f"Warning: Failed to initialize Translator. {e}")
    translator = None

class TranslationRequest(BaseModel):
    text: str

class TranslationResponse(BaseModel):
    result: str

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/text2gloss", response_model=TranslationResponse)
async def text_to_gloss(req: TranslationRequest):
    if not translator:
        return TranslationResponse(result="Error: Translator not initialized (Check API Key).")
    try:
        result = translator.text_to_gloss(req.text)
        return TranslationResponse(result=result)
    except Exception as e:
        return TranslationResponse(result=f"API Error: {str(e)}")

@app.post("/api/gloss2text", response_model=TranslationResponse)
async def gloss_to_text(req: TranslationRequest):
    if not translator:
        return TranslationResponse(result="Error: Translator not initialized (Check API Key).")
    try:
        result = translator.gloss_to_text(req.text)
        return TranslationResponse(result=result)
    except Exception as e:
        return TranslationResponse(result=f"API Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
