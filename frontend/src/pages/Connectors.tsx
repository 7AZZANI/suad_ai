import { useEffect, useState } from "react";
import { api } from "../api";

interface ToolRow {
  name: string;
  description: string;
  scope: string;
  risk_level: string;
  parameters: Record<string, unknown>;
}

export default function Connectors() {
  const [tools, setTools] = useState<ToolRow[]>([]);
  const [tel, setTel] = useState<Record<string, unknown>>();
  const [mem, setMem] = useState<Record<string, unknown>>();

  useEffect(() => {
    api.get<ToolRow[]>("/api/permissions/tools").then(setTools);
    api.get<Record<string, unknown>>("/api/telephony/status").then(setTel);
    api.get<Record<string, unknown>>("/api/memory/status").then(setMem);
  }, []);

  return (
    <div>
      <h1 className="page-title">Connectors</h1>
      <p className="page-sub">
        Business tools the agent can call, plus integration status. Add new
        tools in <code>backend/app/tools/builtin.py</code>.
      </p>

      <div className="grid cols-2">
        <div className="card">
          <h3>Telephony integration</h3>
          <pre>{JSON.stringify(tel, null, 2)}</pre>
        </div>
        <div className="card">
          <h3>Knowledge / RAG integration</h3>
          <pre>{JSON.stringify(mem, null, 2)}</pre>
        </div>
      </div>

      <div className="card">
        <h3>Tool connectors ({tools.length})</h3>
        {tools.map((t) => (
          <div key={t.name} style={{ borderBottom: "1px solid var(--line)", padding: "10px 0" }}>
            <div className="row">
              <b>{t.name}</b>
              <span className="badge muted">{t.scope}</span>
              <div className="spacer" />
              <span className="badge warn">{t.risk_level}</span>
            </div>
            <div className="kv">{t.description}</div>
            <details>
              <summary className="kv" style={{ cursor: "pointer" }}>schema</summary>
              <pre>{JSON.stringify(t.parameters, null, 2)}</pre>
            </details>
          </div>
        ))}
      </div>
    </div>
  );
}
