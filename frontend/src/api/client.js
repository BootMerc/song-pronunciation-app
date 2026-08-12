const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function extractErrorMessage(response) {
  let body;
  try {
    body = await response.json();
  } catch {
    return `Request failed (${response.status})`;
  }
  // FastAPI validation errors: {"detail": [{"msg": "...", "loc": [...]}]}
  // FastAPI HTTPException: {"detail": "some string"}
  if (Array.isArray(body?.detail)) {
    return body.detail.map((item) => item.msg).join("; ");
  }
  if (typeof body?.detail === "string") {
    return body.detail;
  }
  return `Request failed (${response.status})`;
}

async function postJSON(path, payload) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(await extractErrorMessage(response));
  }
  return response.json();
}

export function resolveSong(title, artist) {
  return postJSON("/songs/resolve", { title, artist });
}

export function resolveFromUrl(url) {
  return postJSON("/songs/from-url", { url });
}

export function submitManualLyrics(lyrics) {
  return postJSON("/lyrics/manual", { lyrics });
}

export function translateLines(lines) {
  return postJSON("/lyrics/translate", { lines });
}
