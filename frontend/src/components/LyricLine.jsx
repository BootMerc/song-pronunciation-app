import { useEffect, useRef } from "react";

function formatTimestamp(ms) {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

export default function LyricLine({ line, isActive, showRomanized, showFriendly, translation }) {
  const ref = useRef(null);
  const isBlank = line.original.trim() === "";

  // Smoothly scroll the active line into the middle of the viewport as
  // the song plays — the animation makes it feel like the song is
  // driving the screen, not the other way around.
  useEffect(() => {
    if (isActive && ref.current) {
      ref.current.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [isActive]);

  if (isBlank) {
    return <div className="h-5" aria-hidden="true" />;
  }

  return (
    <div
      ref={ref}
      className={`group rounded-xl border px-5 py-3.5 transition-all duration-300 ${
        isActive
          ? "border-gold/40 bg-ink-900 shadow-lg shadow-gold/10"
          : "border-transparent hover:border-ink-800 hover:bg-ink-900/40"
      }`}
    >
      <div className="flex items-baseline gap-3">
        {line.timestamp_ms != null && (
          <span
            className={`flex-shrink-0 font-mono text-xs tabular-nums transition-colors duration-300 ${
              isActive ? "text-gold/60" : "text-paper-faint"
            }`}
          >
            {formatTimestamp(line.timestamp_ms)}
          </span>
        )}
        <p
          lang="und"
          className={`font-script transition-colors duration-300 ${
            isActive ? "text-xl text-gold" : "text-lg text-paper"
          }`}
        >
          {line.original}
        </p>
      </div>

      {showRomanized && line.romanized !== line.original && (
        <p className="mt-1.5 font-body text-sm text-paper-muted leading-relaxed">
          {line.romanized}
        </p>
      )}

      {showFriendly && line.friendly !== line.original && (
        <p
          className="mt-1 -rotate-[0.5deg] font-hand text-lg text-sage leading-relaxed"
          aria-label={`Pronounced: ${line.friendly}`}
        >
          ↳ {line.friendly}
        </p>
      )}

      {translation && (
        <p className="mt-1.5 border-t border-ink-800/60 pt-1.5 font-body text-sm italic text-paper-faint leading-relaxed">
          {translation}
        </p>
      )}

      {!line.supported && (
        <p className="mt-1 text-xs text-paper-faint/60">
          pronunciation not yet available for this script
        </p>
      )}
    </div>
  );
}
