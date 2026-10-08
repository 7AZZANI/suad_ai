import { useEffect, useState } from "react";
import { api } from "../api";

interface Call {
  id: string; provider: string; direction: string; from: string;
  to: string; status: string; transcript: string; created_at: string;
}

export default function CallLogs() {
  const [calls, setCalls] = useState<Call[]>([]);
  const [status, setStatus] = useState<Record<string, unknown>>();

  async function load() {
    setCalls(await api.get<Call[]>("/api/telephony/calls?limit=100"));
    setStatus(await api.get("/api/telephony/status"));
  }
  useEffect(() => {
    load();
  }, []);

  return (
    <div>
      <h1 className="page-title">Call Logs</h1>
      <p className="page-sub">
        Inbound/outbound telephony sessions. Provider-agnostic — same view for
        LiveKit/SIP or Twilio.
      </p>

      <div className="card">
        <div className="row">
          <h3 style={{ margin: 0 }}>Telephony status</h3>
          <div className="spacer" />
          <button className="ghost" onClick={load}>Refresh</button>
        </div>
        <pre>{JSON.stringify(status, null, 2)}</pre>
      </div>

      <div className="card">
        <h3>Sessions ({calls.length})</h3>
        {calls.length === 0 && (
          <div className="kv">
            No calls yet. POST a webhook to{" "}
            <code>/api/telephony/twilio/webhook</code> or{" "}
            <code>/api/telephony/livekit/webhook</code> to simulate one.
          </div>
        )}
        {calls.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>Time</th><th>Provider</th><th>From → To</th>
                <th>Status</th><th>Transcript</th>
              </tr>
            </thead>
            <tbody>
              {calls.map((c) => (
                <tr key={c.id}>
                  <td>{new Date(c.created_at).toLocaleString()}</td>
                  <td>{c.provider}</td>
                  <td>{c.from || "?"} → {c.to || "?"}</td>
                  <td><span className="badge muted">{c.status}</span></td>
                  <td>{c.transcript || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
