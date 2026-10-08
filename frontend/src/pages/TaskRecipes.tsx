import { useEffect, useState } from "react";
import { api } from "../api";

interface RecipeDetail {
  name: string;
  title: string;
  description: string;
  tools: string[];
  guidance: string;
  steps: string[];
}

export default function TaskRecipes() {
  const [list, setList] = useState<RecipeDetail[]>([]);
  const [sel, setSel] = useState<RecipeDetail | null>(null);

  useEffect(() => {
    api.get<RecipeDetail[]>("/api/tasks").then(setList);
  }, []);

  async function open(name: string) {
    setSel(await api.get<RecipeDetail>(`/api/tasks/${name}`));
  }

  return (
    <div>
      <h1 className="page-title">Task Recipes</h1>
      <p className="page-sub">
        Declarative playbooks (YAML in <code>backend/app/tasks/recipes/</code>).
        Edit and they reload — no restart needed.
      </p>
      <div className="grid cols-2">
        <div className="card">
          <h3>Recipes</h3>
          <table>
            <tbody>
              {list.map((r) => (
                <tr key={r.name}>
                  <td><b>{r.title}</b><div className="kv">{r.description}</div></td>
                  <td style={{ width: 90 }}>
                    <button className="ghost" onClick={() => open(r.name)}>
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="card">
          <h3>{sel ? sel.title : "Select a recipe"}</h3>
          {sel && (
            <>
              <div className="kv">{sel.description}</div>
              <p><b>Tools:</b> {sel.tools.join(", ") || "—"}</p>
              <p><b>Guidance:</b><br />{sel.guidance}</p>
              <b>Steps</b>
              <ol>
                {sel.steps.map((s, i) => (
                  <li key={i} className="kv">{s}</li>
                ))}
              </ol>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
