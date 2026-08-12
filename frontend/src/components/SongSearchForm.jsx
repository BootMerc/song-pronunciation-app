import { useState } from "react";

const TABS = [
  { id: "text", label: "Title + artist" },
  { id: "url", label: "YouTube link" },
];

export default function SongSearchForm({
  onSearch,
  onUrlSearch,
  loading,
  initialTitle = "",
  initialArtist = "",
}) {
  const [mode, setMode] = useState("text");
  const [title, setTitle] = useState(initialTitle);
  const [artist, setArtist] = useState(initialArtist);
  const [url, setUrl] = useState("");

  function handleTextSubmit(event) {
    event.preventDefault();
    if (!title.trim() || !artist.trim()) return;
    onSearch(title.trim(), artist.trim());
  }

  function handleUrlSubmit(event) {
    event.preventDefault();
    if (!url.trim()) return;
    onUrlSearch(url.trim());
  }

  return (
    <div className="animate-fade-up rounded-2xl border border-ink-800 bg-ink-900/60 p-5 shadow-lg backdrop-blur-sm">

      {/* Mode tabs */}
      <div className="mb-4 flex gap-1 rounded-lg bg-ink-950/60 p-1">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setMode(tab.id)}
            className={`flex-1 rounded-md py-1.5 text-sm font-medium transition-all duration-200 ${
              mode === tab.id
                ? "bg-ink-800 text-paper shadow-sm"
                : "text-paper-faint hover:text-paper-muted"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {mode === "text" ? (
        <form onSubmit={handleTextSubmit} className="flex flex-col gap-3">
          <div className="flex flex-col gap-3 sm:flex-row">
            <input
              type="text"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Song title"
              aria-label="Song title"
              disabled={loading}
              className="flex-1 rounded-xl border border-ink-700 bg-ink-950/50 px-4 py-3
                         text-paper placeholder-paper-faint outline-none ring-0
                         transition-all duration-200
                         focus-visible:border-gold focus-visible:ring-2 focus-visible:ring-gold/20
                         disabled:opacity-50"
            />
            <input
              type="text"
              value={artist}
              onChange={(event) => setArtist(event.target.value)}
              placeholder="Artist"
              aria-label="Artist"
              disabled={loading}
              className="flex-1 rounded-xl border border-ink-700 bg-ink-950/50 px-4 py-3
                         text-paper placeholder-paper-faint outline-none ring-0
                         transition-all duration-200
                         focus-visible:border-gold focus-visible:ring-2 focus-visible:ring-gold/20
                         disabled:opacity-50"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !title.trim() || !artist.trim()}
            className="group relative w-full overflow-hidden rounded-xl bg-gold px-6 py-3
                       font-semibold text-ink-950 shadow-md transition-all duration-200
                       hover:shadow-gold/25 hover:shadow-lg hover:-translate-y-0.5
                       active:translate-y-0 disabled:opacity-40 disabled:hover:translate-y-0
                       disabled:hover:shadow-md"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-ink-950/30 border-t-ink-950" />
                Looking…
              </span>
            ) : (
              "Find lyrics"
            )}
          </button>
        </form>
      ) : (
        <form onSubmit={handleUrlSubmit} className="flex flex-col gap-3">
          <input
            type="text"
            value={url}
            onChange={(event) => setUrl(event.target.value)}
            placeholder="https://youtube.com/watch?v=..."
            aria-label="YouTube link"
            disabled={loading}
            className="w-full rounded-xl border border-ink-700 bg-ink-950/50 px-4 py-3
                       text-paper placeholder-paper-faint outline-none ring-0
                       font-mono text-sm
                       transition-all duration-200
                       focus-visible:border-gold focus-visible:ring-2 focus-visible:ring-gold/20
                       disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !url.trim()}
            className="group relative w-full overflow-hidden rounded-xl bg-gold px-6 py-3
                       font-semibold text-ink-950 shadow-md transition-all duration-200
                       hover:shadow-gold/25 hover:shadow-lg hover:-translate-y-0.5
                       active:translate-y-0 disabled:opacity-40 disabled:hover:translate-y-0
                       disabled:hover:shadow-md"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-ink-950/30 border-t-ink-950" />
                Looking…
              </span>
            ) : (
              "Find lyrics"
            )}
          </button>
        </form>
      )}
    </div>
  );
}
