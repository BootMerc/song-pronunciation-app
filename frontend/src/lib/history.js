/**
 * Search history, stored client-side (localStorage) rather than on the
 * backend. This app has no accounts and runs from a single browser, and
 * Render's free tier has no persistent disk — server-side SQLite history
 * would reset on close to every 15-minute idle spin-down once actually
 * deployed, which would make the feature nearly useless in practice.
 * localStorage persists indefinitely on this machine, in this browser,
 * for free, independent of anything the backend does.
 *
 * Trade-off worth knowing: history is local to this browser/device —
 * it won't follow you to a different machine or survive clearing site
 * data. For a single-user app with no accounts, that's the expected
 * shape of "history" anyway (same as browser history itself).
 */

const STORAGE_KEY = "songbook:history";
const MAX_ENTRIES = 50;

export function recordHistoryEntry({ title, artist, video, lyricsFound }) {
  const entry = {
    title,
    artist,
    videoId: video?.video_id ?? null,
    thumbnailUrl: video?.thumbnail_url ?? null,
    lyricsFound,
    searchedAt: Date.now(),
  };

  try {
    const existing = getHistory();
    const updated = [entry, ...existing].slice(0, MAX_ENTRIES);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch {
    // Storage can fail (private browsing, quota exceeded, disabled) —
    // history is a nice-to-have, not core functionality, so fail quietly
    // rather than breaking the search that triggered this.
  }
}

export function getHistory() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}
