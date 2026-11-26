// ss/api.js  — load BEFORE the screen scripts in the HTML.
const BASE = ""; // same-origin (served by FastAPI).

async function j(method, path, body) {
  const res = await fetch(BASE + path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const text = await res.text();
    let msg = `Error ${res.status}: ${res.statusText}`;
    try {
      const parsed = JSON.parse(text);
      if (parsed.error) msg = parsed.error;
    } catch(e) {}
    throw new Error(msg);
  }
  return res.status === 204 ? null : res.json();
}

window.api = {
  // --- live master Excel file ---
  excelInfo:   () => j("GET",  "/api/excel/info"),
  excelOpen:   () => j("POST", "/api/excel/open"),
  excelReveal: () => j("POST", "/api/excel/reveal"),
  // --- existing endpoints ---
  filters:  ()                 => j("GET",  "/api/filters"),   // library distinct values + master taxonomy
  roster:   ()                 => j("GET",  "/api/roster"),    // master player list (lazy; loads classifier only)
  search:   (q, filters)       => {
    const params = { q: q || "" };
    if (filters) {
      if (filters.player) params.player = filters.player;
      if (filters.event) params.event = filters.event;
      if (filters.mood) params.mood = filters.mood;
      if (filters.action) params.action = filters.action;
      if (filters.jersey) params.jersey_color = filters.jersey;
    }
    return j("GET", `/api/search?` + new URLSearchParams(params));
  },
  metadata: (id)               => j("GET",  `/api/metadata?id=${encodeURIComponent(id)}`),
  // Activity log: { username, actionType, details } — saved locally, auto-synced when online.
  activity: (body)             => j("POST", "/api/activity", body),
  thumbURL: (id)               => `${BASE}/api/thumb?id=${encodeURIComponent(id)}`,   // use as <img src>
  // Logs "tagging_start" (user + server time) once the tagging run has actually started.
  startTagging: (folder, opts) => j("POST", "/api/start", { folder, ...opts }).then(res => {
    if (window.SS_USER) window.api.activity({ username: window.SS_USER, actionType: 'tagging_start' }).catch(() => {});
    return res;
  }),
  stopTagging:  ()             => j("POST", "/api/stop"),
  progress: ()                 => j("GET",  "/api/progress"),
  browse:   (start)            => window.openFolderPicker(start),    // in-app folder browser, resolves {folder} ("" if cancelled)

  // --- new endpoints ---
  save:     (id, fields)       => j("POST", `/api/edit/${encodeURIComponent(id)}`, fields),
  verify:   (id)               => j("GET",  `/api/verify?id=${encodeURIComponent(id)}`),
  resolveFace: (payload)       => j("POST", "/api/face/resolve", payload),
  refresh:  ()                 => j("POST", "/api/refresh"),   // sync library with disk
};
