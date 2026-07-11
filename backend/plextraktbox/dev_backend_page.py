"""HTML landing page shown at http://localhost:8000 when ENV=dev."""

from __future__ import annotations

DEV_BACKEND_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>plextraktbox dev backend</title>
    <style>
      :root {
        color-scheme: light dark;
        --bg: #0f1419;
        --panel: #1a2332;
        --border: #2d3a4f;
        --text: #e7edf5;
        --muted: #9aa8bc;
        --accent: #339af0;
        --ok: #51cf66;
        --bad: #ff6b6b;
        --pending: #ffd43b;
      }
      @media (prefers-color-scheme: light) {
        :root {
          --bg: #f4f6f8;
          --panel: #ffffff;
          --border: #d8dee9;
          --text: #1f2937;
          --muted: #64748b;
        }
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        min-height: 100vh;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: radial-gradient(circle at top, #1e293b 0%, var(--bg) 55%);
        color: var(--text);
        display: grid;
        place-items: center;
        padding: 2rem 1rem;
      }
      main {
        width: min(100%, 34rem);
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 1rem;
        padding: 1.75rem;
        box-shadow: 0 18px 40px rgba(0, 0, 0, 0.25);
      }
      h1 {
        margin: 0 0 0.35rem;
        font-size: 1.5rem;
        letter-spacing: -0.02em;
      }
      p { margin: 0.75rem 0; line-height: 1.55; color: var(--muted); }
      a { color: var(--accent); }
      code {
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: 0.92em;
        background: rgba(127, 127, 127, 0.15);
        padding: 0.1rem 0.35rem;
        border-radius: 0.25rem;
      }
      .status-row {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        flex-wrap: wrap;
        margin-top: 1.25rem;
        padding-top: 1.25rem;
        border-top: 1px solid var(--border);
      }
      .badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.35rem 0.65rem;
        border-radius: 999px;
        font-size: 0.875rem;
        font-weight: 600;
        border: 1px solid var(--border);
        background: rgba(127, 127, 127, 0.08);
        transition: color 0.35s ease, border-color 0.35s ease, background 0.35s ease;
      }
      .badge[data-state="ok"] {
        color: var(--ok);
        border-color: color-mix(in srgb, var(--ok) 45%, var(--border));
      }
      .badge[data-state="error"] {
        color: var(--bad);
        border-color: color-mix(in srgb, var(--bad) 45%, var(--border));
      }
      .badge[data-state="pending"] {
        color: var(--pending);
        border-color: color-mix(in srgb, var(--pending) 45%, var(--border));
      }
      .badge-icon {
        width: 0.875rem;
        height: 0.875rem;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
      }
      .badge-icon .check {
        font-size: 0.875rem;
        line-height: 1;
      }
      .spinner {
        width: 0.875rem;
        height: 0.875rem;
        border: 2px solid currentColor;
        border-right-color: transparent;
        border-radius: 50%;
        animation: spin 0.7s linear infinite;
        flex-shrink: 0;
      }
      @keyframes spin {
        to { transform: rotate(360deg); }
      }
      button {
        appearance: none;
        border: 1px solid var(--border);
        background: rgba(127, 127, 127, 0.08);
        color: var(--text);
        border-radius: 0.5rem;
        padding: 0.45rem 0.85rem;
        font: inherit;
        cursor: pointer;
      }
      button:hover { border-color: var(--accent); color: var(--accent); }
      button:disabled { opacity: 0.6; cursor: wait; transition: opacity 0.2s ease; }
      .links { margin-top: 1rem; display: flex; gap: 1rem; flex-wrap: wrap; }
    </style>
  </head>
  <body>
    <main>
      <h1>plextraktbox — dev backend</h1>
      <p>
        The UI with hot reload runs on the Vite dev server at
        <a href="http://localhost:5173">http://localhost:5173</a>.
      </p>
      <p>JSON API routes are available under <code>/api</code> on this server.</p>

      <div class="status-row">
        <span id="api-badge" class="badge" data-state="pending" aria-live="polite">
          <span id="badge-icon" class="badge-icon" aria-hidden="true">
            <span class="spinner"></span>
          </span>
          <span id="badge-label">API</span>
        </span>
        <button id="check-api" type="button">Check API status</button>
      </div>

      <div class="links">
        <a href="http://localhost:5173">Open UI (:5173)</a>
        <a href="/docs">OpenAPI docs</a>
        <a href="/api/health">/api/health</a>
      </div>
    </main>
    <script>
      const badge = document.getElementById("api-badge");
      const badgeIcon = document.getElementById("badge-icon");
      const badgeLabel = document.getElementById("badge-label");
      const button = document.getElementById("check-api");
      const MIN_CHECK_MS = 750;

      function wait(ms) {
        return new Promise((resolve) => setTimeout(resolve, ms));
      }

      let lastVersion = null;

      function setIcon(mode) {
        if (mode === "spinner") {
          badgeIcon.innerHTML = '<span class="spinner"></span>';
          badgeIcon.hidden = false;
        } else if (mode === "check") {
          badgeIcon.innerHTML = '<span class="check">✓</span>';
          badgeIcon.hidden = false;
        } else {
          badgeIcon.innerHTML = "";
          badgeIcon.hidden = true;
        }
      }

      function setPending({ keepVersion = false } = {}) {
        badge.dataset.state = "pending";
        setIcon("spinner");
        badgeLabel.textContent =
          keepVersion && lastVersion ? "API · v" + lastVersion : "API";
      }

      function setOk(version) {
        lastVersion = version;
        badge.dataset.state = "ok";
        setIcon("check");
        badgeLabel.textContent = "API · v" + version;
      }

      function setError() {
        badge.dataset.state = "error";
        setIcon("none");
        badgeLabel.textContent = "API unreachable";
      }

      async function checkHealth({ animate = false } = {}) {
        setPending({ keepVersion: animate });
        button.disabled = true;
        try {
          const requests = [
            fetch("/api/health", { headers: { Accept: "application/json" } }),
          ];
          if (animate) {
            requests.push(wait(MIN_CHECK_MS));
          }
          const [response] = await Promise.all(requests);
          if (!response.ok) throw new Error("HTTP " + response.status);
          const data = await response.json();
          setOk(data.version || "?");
        } catch (error) {
          setError();
          console.error(error);
        } finally {
          button.disabled = false;
        }
      }

      button.addEventListener("click", () => checkHealth({ animate: true }));
      checkHealth();

      // Reload this page when uvicorn restarts after a Python file change.
      let lastRevision = null;
      async function watchRevision() {
        try {
          const response = await fetch("/api/dev/revision", {
            headers: { Accept: "application/json" },
          });
          if (!response.ok) return;
          const data = await response.json();
          if (lastRevision !== null && data.started_at !== lastRevision) {
            location.reload();
            return;
          }
          lastRevision = data.started_at;
        } catch {
          // Backend is restarting; keep polling.
        }
      }
      setInterval(watchRevision, 1500);
      watchRevision();
    </script>
  </body>
</html>"""
