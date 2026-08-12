import { useState } from "react";

export default function ManualLyricsInput({ onSubmit, loading }) {
  const [text, setText] = useState("");

  function handleSubmit(event) {
    event.preventDefault();
    if (!text.trim()) return;
    onSubmit(text);
  }

  return (
    <div className="rounded-2xl border border-ink-800 bg-ink-900/60 p-6 backdrop-blur-sm">
      <div className="mb-4 flex items-start gap-3">
        <span className="mt-0.5 text-2xl select-none" aria-hidden="true">📋</span>
        <div>
          <p className="font-display text-lg text-paper leading-snug">
            Lyrics not found automatically
          </p>
          <p className="mt-1 text-sm text-paper-muted leading-relaxed">
            Paste the original lyrics below and I'll work out the pronunciation.
            Any supported language works — you just need the original script, not a romanization.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <textarea
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder={"Paste lyrics here in their original script\n（日本語, 한국어, 中文, हिन्दी, العربية…）"}
          aria-label="Paste lyrics"
          rows={8}
          disabled={loading}
          className="w-full rounded-xl border border-ink-700 bg-ink-950/50 px-4 py-3
                     font-script text-paper placeholder-paper-faint/60 outline-none
                     transition-all duration-200 leading-relaxed resize-none
                     focus-visible:border-gold focus-visible:ring-2 focus-visible:ring-gold/20
                     disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading || !text.trim()}
          className="mt-3 w-full rounded-xl border border-sage-dim bg-sage/10 px-5 py-2.5
                     font-medium text-sage text-sm transition-all duration-200
                     hover:bg-sage/20 hover:border-sage active:scale-[0.99]
                     disabled:opacity-40 disabled:hover:bg-sage/10"
        >
          {loading ? "Working it out…" : "Get pronunciation"}
        </button>
      </form>
    </div>
  );
}
