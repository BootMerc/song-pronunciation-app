import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import SongSearchForm from "../components/SongSearchForm.jsx";
import YouTubePlayer from "../components/YouTubePlayer.jsx";
import LyricsPanel from "../components/LyricsPanel.jsx";
import ManualLyricsInput from "../components/ManualLyricsInput.jsx";
import { useSongLookup } from "../hooks/useSongLookup.js";

// A handful of real songs in the supported scripts as example hints —
// changes every session without a server call, just looks alive.
const EXAMPLE_HINTS = [
  { title: "Lemon", artist: "Kenshi Yonezu", script: "米津玄師「Lemon」" },
  { title: "Spring Day", artist: "BTS", script: "봄날" },
  { title: "Ai De Jiu Shi Ni", artist: "Faye Wong", script: "愛的就是你" },
  { title: "Kal Ho Naa Ho", artist: "Sonu Nigam", script: "कल हो ना हो" },
  { title: "Hasbi Rabbi Jalallah", artist: "Maher Zain", script: "حسبي ربي" },
  { title: "Tera Yaar Hoon Main", artist: "Arijit Singh", script: "ਤੇਰਾ ਯਾਰ ਹੂੰ ਮੈਂ" },
];

const HINT = EXAMPLE_HINTS[Math.floor(Math.random() * EXAMPLE_HINTS.length)];

export default function SearchPage() {
  const { song, loading, error, search, searchFromUrl, pasteLyrics } = useSongLookup();
  const [currentTimeMs, setCurrentTimeMs] = useState(0);
  const [prefill, setPrefill] = useState({ title: "", artist: "", key: 0 });
  const location = useLocation();

  useEffect(() => {
    const revisit = location.state;
    if (revisit?.title && revisit?.artist) {
      search(revisit.title, revisit.artist);
    }
  }, [location.state, search]);

  async function handleUrlSearch(url) {
    const result = await searchFromUrl(url);
    if (result && !result.lyrics_found && result.guessed_title) {
      setPrefill((prev) => ({
        title: result.guessed_title,
        artist: result.guessed_artist,
        key: prev.key + 1,
      }));
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 pt-8 pb-16 sm:px-8">
      <SongSearchForm
        key={prefill.key}
        onSearch={search}
        onUrlSearch={handleUrlSearch}
        loading={loading}
        initialTitle={prefill.title}
        initialArtist={prefill.artist}
      />

      {error && (
        <div className="animate-fade-up mt-4 rounded-xl border border-sage-dim/40 bg-ink-900/60 px-4 py-3 text-sm text-paper-muted">
          {error}
        </div>
      )}

      {/* Empty state — shows personality instead of a grey one-liner */}
      {!song && !loading && !error && (
        <div className="animate-fade-up mt-16 flex flex-col items-center gap-6 text-center">
          <div className="flex flex-col items-center gap-2">
            <p className="font-display text-2xl text-paper/80">
              {HINT.script}
            </p>
            <p className="text-sm text-paper-faint">
              Try <button
                type="button"
                onClick={() => search(HINT.title, HINT.artist)}
                className="text-gold underline-offset-2 hover:underline transition-colors"
              >
                {HINT.title} — {HINT.artist}
              </button>
            </p>
          </div>
          <div className="flex flex-wrap justify-center gap-2 text-xs text-paper-faint/60">
            <span>Japanese</span><span>·</span>
            <span>Korean</span><span>·</span>
            <span>Chinese</span><span>·</span>
            <span>Hindi</span><span>·</span>
            <span>Arabic</span><span>·</span>
            <span>Punjabi</span><span>·</span>
            <span>Russian</span><span>·</span>
            <span>Greek</span><span>+</span>
            <span>more</span>
          </div>
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="animate-fade-up mt-8 flex flex-col gap-4">
          <div className="h-48 rounded-2xl bg-ink-900/60 animate-pulse" />
          <div className="flex flex-col gap-2">
            {[...Array(5)].map((_, i) => (
              <div
                key={i}
                className="h-14 rounded-xl bg-ink-900/40 animate-pulse"
                style={{ animationDelay: `${i * 60}ms` }}
              />
            ))}
          </div>
        </div>
      )}

      {song && !loading && (
        <div className="mt-8 flex flex-col gap-6">
          {song.guessed_title && (
            <p className="animate-fade-up text-xs text-paper-faint">
              Matched as{" "}
              <span className="text-paper-muted">{song.guessed_title}</span>
              {" — "}
              <span className="text-paper-muted">{song.guessed_artist}</span>.
              Not right? Edit above and search again.
            </p>
          )}

          {song.video && (
            <div className="animate-fade-up flex flex-col gap-3">
              <div className="overflow-hidden rounded-2xl shadow-2xl shadow-black/40">
                <YouTubePlayer videoId={song.video.video_id} onTimeUpdate={setCurrentTimeMs} />
              </div>
              <div>
                <p className="font-display text-lg text-paper leading-snug">{song.video.title}</p>
                <p className="text-sm text-paper-muted">{song.video.channel_title}</p>
              </div>
            </div>
          )}

          {song.video_error && (
            <p className="text-xs text-paper-faint">
              Couldn't load a video: {song.video_error}
            </p>
          )}

          {song.instrumental && (
            <p className="animate-fade-up text-paper-muted">
              This track is instrumental — no lyrics to show.
            </p>
          )}

          {song.lyrics_found && !song.instrumental && (
            <div className="animate-fade-up">
              <LyricsPanel
                lines={song.lines}
                currentTimeMs={currentTimeMs}
                synced={song.synced}
              />
            </div>
          )}

          {!song.lyrics_found && !song.instrumental && (
            <div className="animate-fade-up flex flex-col gap-2">
              {song.lyrics_error && (
                <p className="text-xs text-paper-faint">
                  Lyrics lookup hit a snag: {song.lyrics_error}
                </p>
              )}
              <ManualLyricsInput onSubmit={pasteLyrics} loading={loading} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
