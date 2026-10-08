import { useState } from "react";
import { api } from "../api";

interface VoiceResp {
  transcript: string;
  reply: string;
  audio_base64: string;
  content_type: string;
  audio_note: string;
}

export default function VoiceTest() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<VoiceResp | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [ttsText, setTtsText] = useState("Hello, this is Suad AI speaking.");

  async function runVoice() {
    if (!file) return;
    setBusy(true);
    setErr("");
    try {
      const fd = new FormData();
      fd.append("file", file);
      setResult(await api.postForm<VoiceResp>("/api/agents/default/voice", fd));
    } catch (e: any) {
      setErr(e.message || "Voice pipeline failed (is STT configured?)");
    } finally {
      setBusy(false);
    }
  }

  function play(b64: string, ct: string) {
    const audio = new Audio(`data:${ct};base64,${b64}`);
    audio.play();
  }

  return (
    <div>
      <h1 className="page-title">Voice Test</h1>
      <p className="page-sub">
        Full loop: speech-to-text → agent → text-to-speech. TTS has an offline
        tone fallback so this page always produces audio.
      </p>

      <div className="card">
        <h3>TTS quick test</h3>
        <textarea value={ttsText} onChange={(e) => setTtsText(e.target.value)} />
        <button
          style={{ marginTop: 10 }}
          onClick={async () => {
            const r = await api.post<any>("/api/setup/test-tts");
            alert(`TTS provider: ${r.provider}\n${r.detail}`);
          }}
        >
          Check TTS provider
        </button>
      </div>

      <div className="card">
        <h3>Upload audio (wav) for the full voice loop</h3>
        <input
          type="file"
          accept="audio/*"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        <button style={{ marginTop: 12 }} disabled={!file || busy} onClick={runVoice}>
          {busy ? "Processing…" : "Run voice turn"}
        </button>
        {err && <div className="kv" style={{ color: "var(--bad)" }}>{err}</div>}
        {result && (
          <div style={{ marginTop: 14 }}>
            <div className="kv">Transcript: <b>{result.transcript}</b></div>
            <div className="kv">Reply: <b>{result.reply}</b></div>
            <div className="kv">Audio: {result.audio_note}</div>
            <button
              className="ghost"
              onClick={() => play(result.audio_base64, result.content_type)}
            >
              ▶ Play reply
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
