import { useEffect, useState } from "react";
import { api, ProviderResult } from "../api";
import { Badge } from "../components/Layout";

type AllResults = Record<string, ProviderResult>;

export default function SystemStatus() {
  const [ready, setReady] = useState<{ status: string; database: boolean }>();
  const [summary, setSummary] = useState<Record<string, any>>();
  const [results, setResults] = useState<AllResults>();
  const [loading, setLoading] = useState(false);

  async function refresh() {
    setLoading(true);
    try {
      setReady(await api.get("/ready"));
      setSummary(await api.get("/api/setup/summary"));
      setResults(await api.post("/api/setup/test-all"));
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    refresh();
  }, []);

  return (
    <div>
      <h1 className="page-title">System Status</h1>
      <p className="page-sub">
        Live health of every configured provider. Local-first defaults work
        with no cloud accounts.
      </p>

      <div className="row" style={{ marginBottom: 16 }}>
        <button onClick={refresh} disabled={loading}>
          {loading ? "Checking…" : "Re-run all checks"}
        </button>
        <div className="spacer" />
        <span>
          API: <Badge ok={ready?.status === "ok" || ready?.status === "degraded"} />
        </span>
      </div>

      {summary && (
        <div className="card">
          <h3>Active configuration</h3>
          <div className="grid cols-3">
            <div className="kv">LLM: <b>{summary.llm.provider}</b> / {summary.llm.model}</div>
            <div className="kv">STT: <b>{summary.stt.provider}</b></div>
            <div className="kv">TTS: <b>{summary.tts.provider}</b></div>
            <div className="kv">Telephony: <b>{summary.telephony.provider}</b></div>
            <div className="kv">RAG: <b>{String(summary.rag.enabled)}</b> ({summary.rag.provider})</div>
            <div className="kv">DB: <b>{summary.database}</b></div>
          </div>
        </div>
      )}

      <div className="grid cols-3">
        {results &&
          Object.entries(results).map(([name, r]) => (
            <div className="card" key={name}>
              <div className="row">
                <h3 style={{ margin: 0, textTransform: "uppercase" }}>{name}</h3>
                <div className="spacer" />
                <Badge ok={r.ok} />
              </div>
              <div className="kv" style={{ marginTop: 8 }}>
                provider: <b>{r.provider}</b>
              </div>
              <div className="kv">{r.detail}</div>
            </div>
          ))}
      </div>
    </div>
  );
}
