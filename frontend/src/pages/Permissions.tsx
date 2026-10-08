import { useEffect, useState } from "react";
import { api } from "../api";

interface ToolRow {
  name: string;
  description: string;
  scope: string;
  risk_level: string;
}
interface RoleRow { name: string; description: string; scopes: string[] }
interface AuditRow {
  id: string; subject: string; role: string; tool: string;
  risk_level: string; decision: string; success: boolean; created_at: string;
}
interface ApprovalRow {
  id: string; tool: string; subject: string; role: string; arguments: unknown;
}

const RISK_CLASS: Record<string, string> = {
  safe: "ok", confirm: "warn", approval: "warn", blocked: "bad",
};

export default function Permissions() {
  const [tools, setTools] = useState<ToolRow[]>([]);
  const [roles, setRoles] = useState<RoleRow[]>([]);
  const [audit, setAudit] = useState<AuditRow[]>([]);
  const [approvals, setApprovals] = useState<ApprovalRow[]>([]);

  async function load() {
    setTools(await api.get("/api/permissions/tools"));
    setRoles(await api.get("/api/permissions/roles"));
    setAudit(await api.get("/api/permissions/audit?limit=50"));
    setApprovals(await api.get("/api/permissions/approvals?status=pending"));
  }
  useEffect(() => {
    load();
  }, []);

  async function decide(id: string, approve: boolean) {
    await api.post(`/api/permissions/approvals/${id}`, { approve, decided_by: "admin" });
    load();
  }

  return (
    <div>
      <h1 className="page-title">Permissions</h1>
      <p className="page-sub">
        Every tool has a scope + risk level. Nothing executes without passing
        the engine; every call is audited.
      </p>

      <div className="card">
        <h3>Pending approvals</h3>
        {approvals.length === 0 && <div className="kv">No pending requests.</div>}
        {approvals.map((a) => (
          <div className="row" key={a.id} style={{ marginBottom: 8 }}>
            <span><b>{a.tool}</b> by {a.subject} ({a.role})</span>
            <code>{JSON.stringify(a.arguments)}</code>
            <div className="spacer" />
            <button onClick={() => decide(a.id, true)}>Approve</button>
            <button className="ghost" onClick={() => decide(a.id, false)}>
              Reject
            </button>
          </div>
        ))}
      </div>

      <div className="grid cols-2">
        <div className="card">
          <h3>Registered tools</h3>
          <table>
            <thead>
              <tr><th>Tool</th><th>Scope</th><th>Risk</th></tr>
            </thead>
            <tbody>
              {tools.map((t) => (
                <tr key={t.name}>
                  <td><b>{t.name}</b><div className="kv">{t.description}</div></td>
                  <td><code>{t.scope}</code></td>
                  <td>
                    <span className={`badge ${RISK_CLASS[t.risk_level] || "muted"}`}>
                      {t.risk_level}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="card">
          <h3>Roles &amp; scopes</h3>
          <table>
            <tbody>
              {roles.map((r) => (
                <tr key={r.name}>
                  <td><b>{r.name}</b><div className="kv">{r.description}</div></td>
                  <td><code>{r.scopes.join(", ")}</code></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <h3>Audit log</h3>
        <table>
          <thead>
            <tr><th>Time</th><th>Subject</th><th>Tool</th><th>Risk</th><th>Decision</th></tr>
          </thead>
          <tbody>
            {audit.map((a) => (
              <tr key={a.id}>
                <td>{new Date(a.created_at).toLocaleString()}</td>
                <td>{a.subject} ({a.role})</td>
                <td>{a.tool}</td>
                <td>{a.risk_level}</td>
                <td>
                  <span className={`badge ${a.success ? "ok" : "bad"}`}>
                    {a.decision}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
