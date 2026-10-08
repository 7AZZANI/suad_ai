import { useState } from "react";
import { api, ProviderResult } from "../api";
import { Badge } from "../components/Layout";

const STEPS: { key: string; label: string; path: string; hint: string }[] = [
  { key: "database", label: "1. Database", path: "/api/setup/test-database",
    hint: "Postgres (or local SQLite). Run `make docker-up` or use SQLite." },
  { key: "llm", label: "2. LLM", path: "/api/setup/test-llm",
    hint: "Default: local Ollama. Pull a model: `ollama pull qwen3:4b`." },
  { key: "stt", label: "3. Speech-to-Text", path: "/api/setup/test-stt",
    hint: "Default: local faster-whisper." },
  { key: "tts", label: "4. Text-to-Speech", path: "/api/setup/test-tts",
    hint: "Default: Piper, with an offline tone fallback." },
  { key: "qdrant", label: "5. Vector Memory", path: "/api/setup/test-qdrant",
    hint: "Optional RAG via Qdrant. Disable with RAG_ENABLED=false." },
  { key: "telephony", label: "6. Telephony", path: "/api/setup/test-telephony",
    hint: "LiveKit/SIP (local-first) or Twilio (cloud)." },
];

export default function SetupWizard() {
  const [res, setRes] = useState<Record<string, ProviderResult>>({});
  const [busy, setBusy] = useState<string>();

  async function run(step: (typeof STEPS)[number]) {
    setBusy(step.key);
    try {
      const out = await api.post<ProviderResult>(step.path);
      setRes((r) => ({ ...r, [step.key]: out }));
    } catch (e: any) {
      setRes((r) => ({
        ...r,
        [step.key]: { ok: false, provider: "?", detail: e.message },
      }));
    } finally {
      setBusy(undefined);
    }
  }
  async function runAll() {
    for (const s of STEPS) await run(s);
  }

  return (
    <div>
      <h1 className="page-title">Setup Wizard</h1>
      <p className="page-sub">
        Verify each dependency. Optional providers (Qdrant, Telephony) may stay
        as placeholders — the platform still runs.
      </p>
      <div className="row" style={{ marginBottom: 16 }}>
        <button onClick={runAll}>Run all steps</button>
      </div>
      {STEPS.map((s) => {
        const r = res[s.key];
        return (
          <div className="card" key={s.key}>
            <div className="row">
              <h3 style={{ margin: 0 }}>{s.label}</h3>
              <div className="spacer" />
              {r && <Badge ok={r.ok} />}
              <button
                className="ghost"
                onClick={() => run(s)}
                disabled={busy === s.key}
              >
                {busy === s.key ? "Testing…" : "Test"}
              </button>
            </div>
            <div className="kv" style={{ marginTop: 6 }}>{s.hint}</div>
            {r && (
              <div className="kv">
                <b>{r.provider}</b> — {r.detail}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
