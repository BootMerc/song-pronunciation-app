import { useEffect, useMemo, useState } from "react";
import LyricLine from "./LyricLine.jsx";
import { translateLines } from "../api/client.js";

const FONT_SIZES = ["text-sm", "text-base", "text-lg", "text-xl"];

function getActiveLineIndex(lines, currentTimeMs) {
  if (currentTimeMs == null) return -1;
  let active = -1;
  for (const [index, line] of lines.entries()) {
    if (line.timestamp_ms == null) continue;
    if (line.timestamp_ms <= currentTimeMs) {
      active = index;
    } else {
      break; // lines are chronological — first future timestamp ends the scan
    }
  }
  return active;
}

export default function LyricsPanel({ lines, currentTimeMs, synced }) {
  const [showRomanized, setShowRomanized] = useState(true);
  const [showFriendly, setShowFriendly] = useState(true);
  const [fontSizeIndex, setFontSizeIndex] = useState(1);

  const [translations, setTranslations] = useState(null);
  const [translating, setTranslating] = useState(false);
  const [translationError, setTranslationError] = useState(null);
  const [showTranslation, setShowTranslation] = useState(false);

  // Reset translation state when a genuinely new song loads (a new
  // search/paste creates a new `lines` array; time-tick re-renders from
  // video playback don't, so this only fires on an actual song change).
  useEffect(() => {
    setTranslations(null);
    setTranslating(false);
    setTranslationError(null);
    setShowTranslation(false);
  }, [lines]);

  const activeIndex = useMemo(
    () => (synced ? getActiveLineIndex(lines, currentTimeMs) : -1),
    [lines, currentTimeMs, synced],
  );

  async function handleCopy() {
    const text = lines
      .map((line) => (showFriendly ? line.friendly : line.romanized))
      .filter(Boolean)
      .join("\n");
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // Clipboard access can be blocked by the browser; nothing useful to
      // recover here beyond leaving the text selectable on screen.
    }
  }

  async function handleTranslate() {
    if (translations) {
      setShowTranslation((prev) => !prev);
      return;
    }
    setTranslating(true);
    setTranslationError(null);
    try {
      const result = await translateLines(lines.map((line) => line.original));
      setTranslations(result.translations);
      setShowTranslation(true);
    } catch (err) {
      setTranslationError(err.message);
    } finally {
      setTranslating(false);
    }
  }

  function translateButtonLabel() {
    if (translating) return "Translating…";
    if (translations) return showTranslation ? "Hide translation" : "Show translation";
    return "Translate";
  }

  return (
    <div className={FONT_SIZES[fontSizeIndex]}>
      <div className="mb-4 flex flex-wrap items-center gap-4 border-b border-ink-700 pb-3 text-sm">
        <label className="flex items-center gap-2 text-paper-muted">
          <input
            type="checkbox"
            checked={showRomanized}
            onChange={(event) => setShowRomanized(event.target.checked)}
          />
          Standard romanization
        </label>
        <label className="flex items-center gap-2 text-paper-muted">
          <input
            type="checkbox"
            checked={showFriendly}
            onChange={(event) => setShowFriendly(event.target.checked)}
          />
          English-friendly pronunciation
        </label>

        <div className="ml-auto flex items-center gap-2">
          <button
            type="button"
            onClick={() => setFontSizeIndex((i) => Math.max(0, i - 1))}
            disabled={fontSizeIndex === 0}
            aria-label="Decrease text size"
            className="rounded px-2 py-1 text-paper-muted hover:bg-ink-800 disabled:opacity-30"
          >
            A−
          </button>
          <button
            type="button"
            onClick={() => setFontSizeIndex((i) => Math.min(FONT_SIZES.length - 1, i + 1))}
            disabled={fontSizeIndex === FONT_SIZES.length - 1}
            aria-label="Increase text size"
            className="rounded px-2 py-1 text-paper-muted hover:bg-ink-800 disabled:opacity-30"
          >
            A+
          </button>
          <button
            type="button"
            onClick={handleTranslate}
            disabled={translating}
            className="rounded border border-ink-700 px-3 py-1 text-paper-muted hover:border-gold hover:text-gold disabled:opacity-50"
          >
            {translateButtonLabel()}
          </button>
          <button
            type="button"
            onClick={handleCopy}
            className="rounded border border-ink-700 px-3 py-1 text-paper-muted hover:border-gold hover:text-gold"
          >
            Copy
          </button>
        </div>
      </div>

      {translationError && (
        <p className="mb-3 text-xs text-paper-faint">
          Translation isn't available right now: {translationError}
        </p>
      )}

      <div className="flex flex-col gap-1">
        {lines.map((line, index) => (
          <LyricLine
            // eslint-disable-next-line react/no-array-index-key
            key={index}
            line={line}
            isActive={index === activeIndex}
            showRomanized={showRomanized}
            showFriendly={showFriendly}
            translation={showTranslation ? translations?.[index] : undefined}
          />
        ))}
      </div>
    </div>
  );
}
