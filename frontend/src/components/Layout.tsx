import { NavLink, Outlet } from "react-router-dom";

const NAV = [
  ["/", "System Status"],
  ["/setup", "Setup Wizard"],
  ["/providers", "Provider Settings"],
  ["/playground", "Agent Playground"],
  ["/voice", "Voice Test"],
  ["/tasks", "Task Recipes"],
  ["/permissions", "Permissions"],
  ["/connectors", "Connectors"],
  ["/calls", "Call Logs"],
];

export default function Layout() {
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          Suad AI
          <small>AI Voice Agent Platform</small>
        </div>
        <nav className="nav">
          {NAV.map(([to, label]) => (
            <NavLink key={to} to={to} end={to === "/"}>
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}

export function Badge({ ok }: { ok: boolean | undefined }) {
  if (ok === undefined) return <span className="badge muted">unknown</span>;
  return (
    <span className={`badge ${ok ? "ok" : "bad"}`}>{ok ? "ONLINE" : "OFFLINE"}</span>
  );
}
