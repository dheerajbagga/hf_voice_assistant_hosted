let mediaRecorder;
let chunks = [];
let recordedBlob = null;

const recBtn = document.getElementById("recBtn");
const stopBtn = document.getElementById("stopBtn");
const sendBtn = document.getElementById("sendBtn");
const transcriptDiv = document.getElementById("transcript");
const replyDiv = document.getElementById("reply");
const audioEl = document.getElementById("audio");

const BACKEND = (localStorage.getItem("BACKEND_URL") || "http://127.0.0.1:8000").replace(/\/$/, "");

recBtn.onclick = async () => {
  chunks = [];
  recordedBlob = null;
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);
  mediaRecorder.ondataavailable = e => chunks.push(e.data);
  mediaRecorder.onstop = () => {
    recordedBlob = new Blob(chunks, { type: "audio/webm" });
    sendBtn.disabled = false;
  };
  mediaRecorder.start();
  recBtn.disabled = true;
  stopBtn.disabled = false;
  sendBtn.disabled = true;
};

stopBtn.onclick = () => {
  mediaRecorder.stop();
  recBtn.disabled = false;
  stopBtn.disabled = true;
};

sendBtn.onclick = async () => {
  if (!recordedBlob) return;
  transcriptDiv.textContent = "Transcribing...";
  replyDiv.textContent = "—";
  audioEl.src = "";

  // 1) STT
  const form = new FormData();
  form.append("audio", recordedBlob, "input.webm");
  const sttRes = await fetch(`${BACKEND}/stt`, { method: "POST", body: form });
  if (!sttRes.ok) {
    transcriptDiv.textContent = "STT error";
    return;
  }
  const sttData = await sttRes.json();
  const text = sttData.text || "";
  transcriptDiv.textContent = text || "(no speech detected)";

  if (!text) return;

  // 2) Chat
  replyDiv.textContent = "Thinking...";
  const chatRes = await fetch(`${BACKEND}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt: text })
  });
  if (!chatRes.ok) {
    replyDiv.textContent = "LLM error";
    return;
  }
  const chatData = await chatRes.json();
  const reply = chatData.reply || "";
  replyDiv.textContent = reply;

  // 3) TTS
  const ttsRes = await fetch(`${BACKEND}/tts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: reply })
  });
  if (!ttsRes.ok) {
    console.warn("TTS error");
    return;
  }
  const audioBuf = await ttsRes.arrayBuffer();
  const blob = new Blob([audioBuf], { type: "audio/wav" });
  audioEl.src = URL.createObjectURL(blob);
  audioEl.play();
};
