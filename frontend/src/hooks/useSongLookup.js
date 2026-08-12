import { useCallback, useState } from "react";
import { resolveFromUrl, resolveSong, submitManualLyrics } from "../api/client.js";
import { recordHistoryEntry } from "../lib/history.js";

export function useSongLookup() {
  const [song, setSong] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const runLookup = useCallback(async (apiCall) => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiCall();
      setSong(result);
      return result;
    } catch (err) {
      setError(err.message);
      setSong(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const search = useCallback(
    async (title, artist) => {
      const result = await runLookup(() => resolveSong(title, artist));
      if (result) {
        recordHistoryEntry({ title, artist, video: result.video, lyricsFound: result.lyrics_found });
      }
      return result;
    },
    [runLookup],
  );

  const searchFromUrl = useCallback(
    async (url) => {
      const result = await runLookup(() => resolveFromUrl(url));
      if (result) {
        recordHistoryEntry({
          title: result.guessed_title ?? "Unknown title",
          artist: result.guessed_artist ?? "Unknown artist",
          video: result.video,
          lyricsFound: result.lyrics_found,
        });
      }
      return result;
    },
    [runLookup],
  );

  const pasteLyrics = useCallback(async (lyricsText) => {
    setLoading(true);
    setError(null);
    try {
      const result = await submitManualLyrics(lyricsText);
      // Keep whatever video info we already have; only the lyrics side
      // of the song changes when pasting in manually.
      setSong((previous) => ({
        ...(previous ?? { video: null, video_error: null }),
        lyrics_found: true,
        instrumental: false,
        synced: false,
        lines: result.lines,
        lyrics_error: null,
      }));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  return { song, loading, error, search, searchFromUrl, pasteLyrics };
}
