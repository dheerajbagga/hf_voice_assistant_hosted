# Hugging Face Hosted Voice Assistant (Web Frontend + FastAPI Backend)

**Input:** Speech → **STT**  
**LLM:** Text → Text  
**Output:** Text on screen + **TTS** audio playback

No local models needed. Uses **Hugging Face Inference API** for STT, LLM, and TTS.

---

## 🧱 Architecture

```
[Browser Mic] → /stt → Whisper (HF API) → transcript
transcript → /chat → LLM (HF API) → reply text
reply text → /tts → TTS (HF API) → WAV bytes → play in browser
```

- **Frontend:** Plain HTML + JS (MediaRecorder API for mic, fetch() to backend)
- **Backend:** FastAPI with `huggingface-hub` `InferenceClient`
- **Auth:** Your HF token stays on the server (never in the browser)

---

## 🚀 Quick Start

### 1) Backend setup
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# set your Hugging Face token (create at https://huggingface.co/settings/tokens)
export HF_TOKEN=hf_********************************    # PowerShell: $env:HF_TOKEN="hf_***"

# (Optional) choose different hosted models
export STT_MODEL="openai/whisper-small"
export LLM_MODEL="HuggingFaceH4/zephyr-7b-beta"
export TTS_MODEL="espnet/kan-bayashi_ljspeech_vits"

# run the API
uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

### 2) Frontend
Just open `frontend/index.html` in your browser.  
If your backend is not at `http://127.0.0.1:8000`, set it in DevTools console:
```js
localStorage.setItem("BACKEND_URL", "http://localhost:8000")
```

### 3) Use it
- Click **Start Recording**, speak, then **Stop**.  
- Click **Send to Assistant** → it will show the transcript, generate a reply, and play the TTS audio.

---

## 🔧 Notes & Customization

- **Security**: Keep `HF_TOKEN` only on server. Do **not** expose it to the client.
- **Audio format**: Browser records `audio/webm`; backend forwards bytes to HF STT. Most Whisper endpoints accept webm/ogg/wav/mp3.
- **Model choices** (env overrides):
  - STT: `openai/whisper-small`, `openai/whisper-medium`, etc.
  - LLM: `HuggingFaceH4/zephyr-7b-beta`, `mistralai/Mixtral-8x7B-Instruct`
  - TTS: `espnet/kan-bayashi_ljspeech_vits`, `facebook/fastspeech2-en-ljspeech`
- **Latency**: Larger models increase latency; start with smaller ones.
- **CORS**: Enabled for all origins by default (adjust for production).

---

## 🧪 Troubleshooting

- **401 / auth errors** → Ensure `HF_TOKEN` is set and valid.
- **CORS errors** → Confirm backend URL matches your `localStorage BACKEND_URL` or keep defaults.
- **Mic permission** → Allow microphone in the browser.
- **STT fails** → Try shorter recordings (3–5s) and speak clearly; check model names.

---

## 📦 Deploy

- Backend: Deploy FastAPI on a small VM or Platform-as-a-Service (Railway, Render, Azure Web App). Set env vars there.
- Frontend: Serve the static files from any static hosting (or same server as backend with a static route).
- Add HTTPS and restrict CORS origins to your domain in production.

---

## 🔐 Secure Coding Reminders

- Never ship your HF token in the frontend.
- Rate-limit API endpoints if you put it on the internet.
- Log minimally (no raw audio, no secrets).
- Pin dependencies and update regularly.
