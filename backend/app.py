import os
import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from huggingface_hub import InferenceClient
from dotenv import dotenv_values  # <-- reads ONLY the .env file (does not set os.environ)

# --- 1) Secrets: ONLY from system environment (NOT from .env) ---
HF_TOKEN = os.environ.get("HF_TOKEN")  # use system/host env, Docker/CI/Cloud secrets, etc.
if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN not set in the SYSTEM environment (not .env).")

# --- 2) Models: Prefer .env, else fall back to system env, else default ---
# Read key/values from local .env file without polluting process env:
envfile = dotenv_values(".env")  # e.g., {"STT_MODEL": "...", "LLM_MODEL": "...", "TTS_MODEL": "..."}

# If someone accidentally added HF_TOKEN to .env, explicitly ignore it:
if "HF_TOKEN" in envfile:
    # Optional: log a warning instead of printing in production
    print("⚠️  Ignoring HF_TOKEN found in .env. Secrets must come from system environment only.")

def _pick(name: str, default: str) -> str:
    # priority: .env -> system env -> default
    return envfile.get(name) or os.getenv(name) or default

STT_MODEL = _pick("STT_MODEL", "openai/whisper-small")
LLM_MODEL = _pick("LLM_MODEL", "HuggingFaceH4/zephyr-7b-beta")
TTS_MODEL = _pick("TTS_MODEL", "espnet/kan-bayashi_ljspeech_vits")

# --- 3) HF client ---
client = InferenceClient(token=HF_TOKEN)

# --- 4) FastAPI app ---
app = FastAPI(title="HF Voice Assistant Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatBody(BaseModel):
    prompt: str

class TTSBody(BaseModel):
    text: str

@app.get("/health")
def health():
    return {
        "status": "ok",
        "models": {"stt": STT_MODEL, "llm": LLM_MODEL, "tts": TTS_MODEL}
    }

@app.post("/stt")
async def stt(audio: UploadFile = File(...)):
    try:
        contents = await audio.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Empty audio upload")
        text = client.audio_to_text(model=STT_MODEL, audio=io.BytesIO(contents))
        return {"text": text.strip() if isinstance(text, str) else str(text)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT error: {e}")

@app.post("/chat")
def chat(body: ChatBody):
    try:
        prompt = body.prompt.strip()
        if not prompt:
            raise HTTPException(status_code=400, detail="Empty prompt")
        out = client.text_generation(
            model=LLM_MODEL,
            prompt=prompt,
            max_new_tokens=256,
            temperature=0.3,
        )
        return {"reply": out.strip() if isinstance(out, str) else str(out)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {e}")

@app.post("/tts")
def tts(body: TTSBody):
    try:
        text = body.text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="Empty text")
        audio_bytes = client.text_to_speech(model=TTS_MODEL, text=text)
        return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/wav")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {e}")
