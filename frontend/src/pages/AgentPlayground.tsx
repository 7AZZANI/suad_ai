import { useEffect, useState } from "react";
import { api } from "../api";

interface ChatResp {
  conversation_id: string | null;
  reply: string;
  tool_invocations: { tool: string; decision: string; ok?: boolean }[];
  pending_action: { tool_name: string; decision: string; reason: string } | null;
  used_rag: boolean;
  citations: { text: string; score: number }[];
}
type Msg = { role: "user" | "assistant" | "tool"; text: string };

export default function AgentPlayground() {
  const [recipes, setRecipes] = useState<{ name: string; title: string }[]>([]);
  const [recipe, setRecipe] = useState("");
  const [input, setInput] = useState("");
  const [log, setLog] = useState<Msg[]>([]);
  const [conv, setConv] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [pending, setPending] = useState<ChatResp["pending_action"]>(null);

  useEffect(() => {
    api.get<{ name: string; title: string }[]>("/api/tasks").then(setRecipes);
  }, []);

  async function send(text: string, confirm = false) {
    if (!text.trim()) return;
    if (!confirm) setLog((l) => [...l, { role: "user", text }]);
    setBusy(true);
    try {
      const r = await api.post<ChatResp>("/api/agents/default/chat", {
        message: text,
        conversation_id: conv,
        recipe: recipe || null,
        confirm,
      });
      setConv(r.conversation_id);
      r.tool_invocations.forEach((t) =>
        setLog((l) => [
          ...l,
          { role: "tool", text: `tool ${t.tool} → ${t.decision}${t.ok === false ? " (failed)" : ""}` },
        ]),
      );
      setLog((l) => [...l, { role: "assistant", text: r.reply }]);
      setPending(r.pending_action);
    } catch (e: any) {
      setLog((l) => [...l, { role: "assistant", text: `⚠ ${e.message}` }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <h1 className="page-title">Agent Playground</h1>
      <p className="page-sub">
        Chat with the default agent. Tool calls pass the permission engine —
        risky actions surface a confirm/approval gate.
      </p>

      <div className="card">
        <div className="row">
          <label style={{ margin: 0 }}>Task recipe</label>
          <select
            style={{ width: 260 }}
            value={recipe}
            onChange={(e) => setRecipe(e.target.value)}
          >
            <option value="">(none)</option>
            {recipes.map((r) => (
              <option key={r.name} value={r.name}>{r.title}</option>
            ))}
          </select>
          <div className="spacer" />
          <button
            className="ghost"
            onClick={() => {
              setLog([]);
              setConv(null);
              setPending(null);
            }}
          >
            New conversation
          </button>
        </div>

        <div className="chat-log" style={{ marginTop: 16 }}>
          {log.length === 0 && (
            <div className="kv">Try: “What is the status of order 1001?”</div>
          )}
          {log.map((m, i) => (
            <div key={i} className={`msg ${m.role}`}>{m.text}</div>
          ))}
        </div>

        {pending && (
          <div className="card" style={{ background: "#fffbeb", borderColor: "#fbbf24" }}>
            <b>Authorization required</b> — {pending.tool_name} ({pending.decision})
            <div className="kv">{pending.reason}</div>
            <button style={{ marginTop: 8 }} onClick={() => send(log[log.length - 2]?.text ?? "", true)}>
              Confirm &amp; retry
            </button>
          </div>
        )}

        <div className="row">
          <input
            placeholder="Type a message…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !busy) {
                send(input);
                setInput("");
              }
            }}
          />
          <button
            disabled={busy}
            onClick={() => {
              send(input);
              setInput("");
            }}
          >
            {busy ? "…" : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
}
