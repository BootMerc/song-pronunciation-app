import { useEffect, useRef } from "react";

const POLL_INTERVAL_MS = 250;

/**
 * Polls a YouTube player's currentTime while it's ready, calling
 * onTimeUpdate(ms) on each tick. Takes a ref (not the player instance
 * directly) since the player is created asynchronously after the IFrame
 * API script loads, well after this hook first runs.
 */
export function usePlayerTime(playerRef, isReady, onTimeUpdate) {
  const callbackRef = useRef(onTimeUpdate);
  callbackRef.current = onTimeUpdate;

  useEffect(() => {
    if (!isReady) return undefined;

    const interval = setInterval(() => {
      const player = playerRef.current;
      if (player && typeof player.getCurrentTime === "function") {
        callbackRef.current(Math.floor(player.getCurrentTime() * 1000));
      }
    }, POLL_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [playerRef, isReady]);
}
