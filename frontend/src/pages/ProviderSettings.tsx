import { useEffect, useState } from "react";
import { api } from "../api";

// Configuration is intentionally .env-driven (no secrets in the browser).
// This page documents the active selection and how to switch providers.
const SWITCHES = [
  ["LLM → OpenRouter", "LLM_PROVIDER=openrouter\nLLM_BASE_URL=https://openrouter.ai/api/v1\nLLM_API_KEY=...\nLLM_MODEL=qwen/qwen3-32b"],
  ["LLM → OpenAI", "LLM_PROVIDER=openai\nLLM_API_KEY=...\nLLM_MODEL=gpt-4.1-mini"],
  ["LLM → Claude", "LLM_PROVIDER=anthropic\nANTHROPIC_API_KEY=...\nLLM_MODEL=claude-sonnet-4"],
  ["Telephony → Twilio", "TELEPHONY_PROVIDER=twilio\nTWILIO_ACCOUNT_SID=...\nTWILIO_AUTH_TOKEN=...\nTWILIO_PHONE_NUMBER=..."],
];

export default function ProviderSettings() {
  const [summary, setSummary] = useState<Record<string, any>>();
  useEffect(() => {
    api.get<Record<string, any>>("/api/setup/summary").then(setSummary);
  }, []);

  return (
    <div>
      <h1 className="page-title">Provider Settings</h1>
      <p className="page-sub">
        Providers are swapped via <code>.env</code> — no vendor is hardcoded.
        Restart the backend after changing it.
      </p>

      {summary && (
        <div className="card">
          <h3>Currently active</h3>
          <table>
            <tbody>
              <tr><td>LLM</td><td><b>{summary.llm.provider}</b> · {summary.llm.model}</td></tr>
              <tr><td>STT</td><td>{summary.stt.provider} · {summary.stt.model}</td></tr>
              <tr><td>TTS</td><td>{summary.tts.provider} · {summary.tts.voice}</td></tr>
              <tr><td>Telephony</td><td>{summary.telephony.provider}</td></tr>
              <tr><td>RAG</td><td>{String(summary.rag.enabled)} · {summary.rag.provider}</td></tr>
              <tr><td>Database</td><td>{summary.database}</td></tr>
            </tbody>
          </table>
        </div>
      )}

      <div className="grid cols-2">
        {SWITCHES.map(([title, env]) => (
          <div className="card" key={title}>
            <h3>{title}</h3>
            <pre>{env}</pre>
          </div>
        ))}
      </div>
    </div>
  );
}
