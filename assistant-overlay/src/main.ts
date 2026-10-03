import { WSClient } from "./ws/client";
import { OverlayController } from "./ui/overlay";
import { BubbleController } from "./ui/bubble";
import { LipSync } from "./live2d/lipsync";

const client = new WSClient("ws://127.0.0.1:8765/ws", { maxRetries: 3 });
const appEl = document.getElementById("app") as HTMLElement;
const bubbleEl = document.getElementById("bubble") as HTMLElement;
const canvas = document.getElementById("canvas") as HTMLCanvasElement;
const statusText = document.getElementById("status-text") as HTMLElement | null;
const statusDot = document.getElementById("status-dot") as HTMLElement | null;
const wsHint = document.getElementById("ws-hint") as HTMLElement | null;
const overlay = new OverlayController(appEl, client);
const bubble = new BubbleController(bubbleEl);
const lipsync = new LipSync({ params: {} as Record<string, number>, setParam: (_k: string, _v: number) => {} });

function setStatus(state: string) {
  if (statusText) statusText.textContent = `${state} · ${state === "IDLE" ? "siap" : state === "LISTENING" ? "mendengar..." : state === "THINKING" ? "berpikir..." : "bicara..."}`;
  if (statusDot) {
    const col = state === "IDLE" ? "#a6e3a1" : state === "LISTENING" ? "#f38ba8" : state === "THINKING" ? "#f9e2af" : "#89b4fa";
    statusDot.style.background = col;
    statusDot.style.boxShadow = `0 0 8px ${col}`;
  }
}
setStatus("IDLE");
client.on("state", (s: unknown) => {
  if (typeof s === "string") setStatus(s);
});
if (wsHint) {
  client.on("reconnect", () => { wsHint.textContent = "◌"; wsHint.style.color = "#f9e2af"; });
  client.on("message", () => { wsHint.textContent = "●"; wsHint.style.color = "#a6e3a1"; });
}

// --- Mic / PTT / SpeechRecognition ---
const micBtn = document.getElementById("mic-btn") as HTMLButtonElement | null;
const textInput = document.getElementById("text-input") as HTMLInputElement | null;
const sendBtn = document.getElementById("send-btn") as HTMLButtonElement | null;

type SRConstructor = new () => { lang: string; interimResults: boolean; continuous: boolean; onstart: ((e: unknown) => void) | null; onend: ((e: unknown) => void) | null; onerror: ((e: unknown) => void) | null; onresult: ((e: { results: ArrayLike<{ 0: { transcript: string }; isFinal: boolean }> }) => void) | null; start(): void; stop(): void };
let recognition: InstanceType<SRConstructor> | null = null;
let recListening = false;

function getRecognition(): InstanceType<SRConstructor> | null {
  const w = window as unknown as { SpeechRecognition?: SRConstructor; webkitSpeechRecognition?: SRConstructor };
  const Ctor = w.SpeechRecognition ?? w.webkitSpeechRecognition;
  if (!Ctor) return null;
  if (!recognition) {
    recognition = new Ctor();
    recognition.lang = "id-ID";
    recognition.interimResults = true;
    recognition.continuous = false;
    recognition.onstart = () => {
      recListening = true;
      if (micBtn) micBtn.classList.add("listening");
      setStatus("LISTENING");
      client.send({ command: "startListening", word: "manual" });
    };
    recognition.onend = () => {
      recListening = false;
      if (micBtn) micBtn.classList.remove("listening");
    };
    recognition.onerror = () => {
      recListening = false;
      if (micBtn) micBtn.classList.remove("listening");
    };
    recognition.onresult = (e) => {
      let interim = "";
      let finalText = "";
      for (let i = 0; i < e.results.length; i++) {
        const r = e.results[i] as unknown as { 0: { transcript: string }; isFinal: boolean };
        if (r.isFinal) finalText += r[0].transcript + " ";
        else interim += r[0].transcript + " ";
      }
      const txt = (finalText || interim).trim();
      if (txt) bubble.showPartial(txt);
      if (finalText.trim()) {
        const t = finalText.trim();
        // also show as final quickly, then send
        bubble.showFinal(t);
        client.send({ command: "transcript", text: t });
        client.send({ transcript: t });
        // ensure overlay state moves to THINKING; main.ts also handles via server
      }
    };
  }
  return recognition;
}

function startListening() {
  const rec = getRecognition();
  if (!rec) {
    // No Web Speech API (WebKitGTK 4.1 lacks it) — focus text input as fallback
    if (textInput) {
      textInput.focus();
      bubble.showFinal("Mic tidak didukung di WebKit — ketik di bawah lalu Enter ne~");
    }
    setStatus("LISTENING");
    client.send({ command: "startListening", word: "manual" });
    return;
  }
  if (recListening) return;
  try {
    rec.start();
  } catch {}
}

function stopListening() {
  if (!recognition || !recListening) {
    if (textInput && document.activeElement === textInput) {
      // keep focus
    }
    return;
  }
  try {
    recognition.stop();
  } catch {}
}

function sendText() {
  if (!textInput) return;
  const t = textInput.value.trim();
  if (!t) return;
  bubble.showFinal(t);
  client.send({ command: "transcript", text: t });
  client.send({ transcript: t });
  client.send({ type: "stt.final", text: t });
  textInput.value = "";
  setStatus("THINKING");
}

if (micBtn) {
  micBtn.addEventListener("click", () => {
    if (recListening) stopListening();
    else startListening();
  });
}
if (sendBtn) sendBtn.addEventListener("click", sendText);
if (textInput) {
  textInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      sendText();
    }
  });
  // also allow mic focus via input
  textInput.addEventListener("focus", () => {
    if (micBtn) micBtn.classList.remove("listening");
  });
}
// Super+Space global PTT toggle
window.addEventListener("keydown", (e) => {
  const isSuperSpace = (e.metaKey || (e as unknown as { superKey?: boolean }).superKey) && e.code === "Space";
  // also support Ctrl+Space as fallback if Super not delivered by Tauri
  const isCtrlSpace = e.ctrlKey && e.code === "Space";
  if (isSuperSpace || isCtrlSpace) {
    e.preventDefault();
    if (recListening) stopListening();
    else startListening();
  }
  if (e.key === "Escape" && recListening) {
    e.preventDefault();
    stopListening();
    client.send({ command: "cancel" });
  }
});

// Paint a soft placeholder gradient on canvas so it never looks empty
try {
  const ctx = canvas.getContext("2d");
  if (ctx) {
    const g = ctx.createLinearGradient(0, 0, 0, 320);
    g.addColorStop(0, "rgba(137,180,250,0.12)");
    g.addColorStop(1, "rgba(203,166,247,0.08)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, 260, 320);
    ctx.fillStyle = "rgba(255,255,255,0.06)";
    ctx.font = "11px JetBrains Mono";
    ctx.fillText("Live2D placeholder", 70, 310);
  }
} catch {}

let audioCtx: AudioContext | null = null;
let queue: Array<{ b64: string; viseme: { mouthOpen: number }; durationMs: number }> = [];
let playing = false;

function getAudioCtx(): AudioContext {
  if (!audioCtx) audioCtx = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
  if (audioCtx.state === "suspended") void audioCtx.resume();
  return audioCtx;
}

function b64ToBytes(b64: string): Uint8Array {
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return bytes;
}

async function playQueue() {
  if (playing || queue.length === 0) return;
  playing = true;
  const ctx = getAudioCtx();
  while (queue.length > 0) {
    const item = queue.shift()!;
    if (queue.length > 8) queue = queue.slice(-8);
    const bytes = b64ToBytes(item.b64);
    lipsync.pushViseme(item.viseme?.mouthOpen ?? 0.6, item.durationMs ?? 300);
    // Detect mime: WAV header RIFF
    const isWav = bytes.length > 12 && bytes[0] === 0x52 && bytes[1] === 0x49 && bytes[2] === 0x46 && bytes[3] === 0x46;
    let played = false;
    // 1) Preferred: AudioContext (works for WAV PCM via FFMpeg path)
    if (!played) {
      try {
        const ab = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength) as ArrayBuffer;
        const buf = await ctx.decodeAudioData(ab.slice(0));
        const src = ctx.createBufferSource();
        src.buffer = buf;
        src.connect(ctx.destination);
        await new Promise<void>((res) => {
          let done = false;
          const finish = () => { if (!done) { done = true; res(); } };
          src.onended = finish;
          src.start();
          setTimeout(finish, (buf.duration * 1000 + 500) | 0);
        });
        played = true;
      } catch {}
    }
    // 2) Fallback: <audio> with correct MIME (WAV or MP3)
    if (!played) {
      try {
        const mime = isWav ? "audio/wav" : "audio/mpeg";
        const blob = new Blob([bytes], { type: mime });
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.volume = 0.9;
        await new Promise<void>((res) => {
          let done = false;
          const finish = () => { if (!done) { done = true; URL.revokeObjectURL(url); res(); } };
          audio.onended = finish;
          audio.onerror = finish;
          void audio.play().catch(finish);
          setTimeout(finish, (item.durationMs ?? 600) + 1200);
        });
        played = true;
      } catch {}
    }
    if (!played) await new Promise((r) => setTimeout(r, item.durationMs ?? 300));
    lipsync.pushViseme(0, 80);
  }
  playing = false;
}

client.on("message", (msg: unknown) => {
  const m = msg as Record<string, unknown>;
  if (m?.type === "llm.token" && typeof m.text === "string") {
    bubble.appendToken(m.text);
  } else if (m?.type === "transcript.final" && typeof m.text === "string") {
    bubble.showFinal(m.text);
  } else if (m?.type === "tts.chunk" && typeof (m as { audioB64?: string }).audioB64 === "string") {
    const r = m as unknown as { audioB64: string; audio?: string; viseme: { mouthOpen: number }; durationMs: number };
    const b64 = r.audioB64 || r.audio;
    if (b64) {
      queue.push({ b64, viseme: r.viseme ?? { mouthOpen: 0.6 }, durationMs: r.durationMs ?? 600 });
      if (queue.length > 8) queue = queue.slice(-8);
      void playQueue();
    }
  } else if (m?.type === "tts.chunk" && typeof m.audio === "string" && (m.audio as string).length > 100) {
    const r = m as unknown as { audio: string; viseme: { mouthOpen: number }; durationMs: number };
    queue.push({ b64: r.audio, viseme: r.viseme ?? { mouthOpen: 0.6 }, durationMs: r.durationMs ?? 600 });
    if (queue.length > 8) queue = queue.slice(-8);
    void playQueue();
  } else if (m?.type === "error" && typeof (m as { bubble: string }).bubble === "string") {
    bubble.showFinal((m as { bubble: string }).bubble);
  } else if (m?.type === "expression" && typeof (m as { name: string }).name === "string") {
    const name = (m as { name: string }).name;
    if (name && bubbleEl) bubbleEl.dataset.expression = name;
  }
});

let rafId = 0;
function tickRaf() {
  lipsync.tick(16);
  rafId = requestAnimationFrame(tickRaf);
}
tickRaf();

void rafId;
void canvas;

client.connect();
overlay.init();
console.log("Anime Assistant overlay started");
