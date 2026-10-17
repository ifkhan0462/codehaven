import { useEffect, useState } from "react";
import { fetchHealth, type HealthResponse } from "../api/client";

export function StatusBar() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function check() {
      try {
        const data = await fetchHealth();
        if (active) {
          setHealth(data);
          setError(null);
        }
      } catch {
        if (active) {
          setHealth(null);
          setError("Backend offline");
        }
      }
    }

    check();
    const id = setInterval(check, 10000);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, []);

  const ollamaOk = health?.ollama?.reachable;
  const modelOk = health?.ollama?.chat_model_available;

  return (
    <header className="status-bar">
      <div className="brand">
        <span className="brand-icon">{"</>"}</span>
        <div>
          <strong>CodeHaven</strong>
          <span className="tagline">Your code stays on your machine</span>
        </div>
      </div>
      <div className="status-pills">
        <span className={`pill ${health ? "ok" : "bad"}`}>
          API {health ? "online" : error ?? "checking..."}
        </span>
        <span className={`pill ${ollamaOk ? "ok" : "bad"}`}>
          Ollama {ollamaOk ? "ready" : "unavailable"}
        </span>
        <span className={`pill ${modelOk ? "ok" : "warn"}`}>
          {health?.chat_model ?? "qwen2.5-coder:7b"}
          {modelOk ? "" : " (not pulled)"}
        </span>
        <span className="pill ok">Offline mode</span>
      </div>
    </header>
  );
}
