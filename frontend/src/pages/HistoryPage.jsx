import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getHistory } from "../lib/history.js";

function timeAgo(unixMillis) {
  const diffSeconds = Math.floor((Date.now() - unixMillis) / 1000);
  if (diffSeconds < 60) return "just now";
  const minutes = Math.floor(diffSeconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(unixMillis).toLocaleDateString();
}

export default function HistoryPage() {
  const [entries, setEntries] = useState([]);
  const navigate = useNavigate();

  // Read fresh on every mount — navigating here after a new search
  // should show it, and React Router remounts this component on each
  // visit to the route by default, so this is enough (no polling needed).
  useEffect(() => {
    setEntries(getHistory());
  }, []);

  function revisit(entry) {
    navigate("/", { state: { title: entry.title, artist: entry.artist } });
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-10 sm:px-8">
      <h2 className="font-display text-2xl text-paper">Songs you've tried</h2>
      <p className="mt-1 text-xs text-paper-faint">
        Stored on this device only — clearing browser data clears this too.
      </p>

      {entries.length === 0 && (
        <p className="mt-6 text-paper-faint">
          Nothing here yet — songs you look up will show up in this list.
        </p>
      )}

      <div className="mt-6 flex flex-col gap-1">
        {entries.map((entry, index) => (
          <button
            type="button"
            // eslint-disable-next-line react/no-array-index-key
            key={`${entry.title}-${entry.artist}-${entry.searchedAt}-${index}`}
            onClick={() => revisit(entry)}
            className="flex items-center gap-4 rounded-lg border-l-2 border-transparent
                       px-3 py-3 text-left transition-colors hover:border-gold hover:bg-ink-900"
          >
            {entry.thumbnailUrl ? (
              <img
                src={entry.thumbnailUrl}
                alt=""
                className="h-12 w-16 flex-shrink-0 rounded object-cover"
              />
            ) : (
              <div className="h-12 w-16 flex-shrink-0 rounded bg-ink-800" />
            )}
            <div className="min-w-0 flex-1">
              <p className="truncate font-display text-base text-paper">{entry.title}</p>
              <p className="truncate text-sm text-paper-muted">{entry.artist}</p>
            </div>
            <div className="flex flex-shrink-0 flex-col items-end gap-1 text-xs">
              <span className="text-paper-faint">{timeAgo(entry.searchedAt)}</span>
              {!entry.lyricsFound && (
                <span className="text-paper-faint">lyrics not found</span>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
