import { useEffect, useRef, useState } from "react";
import { usePlayerTime } from "../hooks/usePlayerTime.js";

let apiLoadingPromise = null;

function loadYouTubeAPI() {
  if (window.YT?.Player) return Promise.resolve();
  if (apiLoadingPromise) return apiLoadingPromise;

  apiLoadingPromise = new Promise((resolve) => {
    const previous = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = () => {
      previous?.();
      resolve();
    };
    const script = document.createElement("script");
    script.src = "https://www.youtube.com/iframe_api";
    document.head.appendChild(script);
  });
  return apiLoadingPromise;
}

export default function YouTubePlayer({ videoId, onTimeUpdate }) {
  const containerRef = useRef(null);
  const playerRef = useRef(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setIsReady(false);

    loadYouTubeAPI().then(() => {
      if (cancelled || !containerRef.current) return;
      playerRef.current = new window.YT.Player(containerRef.current, {
        videoId,
        playerVars: { rel: 0 },
        events: {
          onReady: () => {
            if (!cancelled) setIsReady(true);
          },
        },
      });
    });

    return () => {
      cancelled = true;
      setIsReady(false);
      playerRef.current?.destroy?.();
      playerRef.current = null;
    };
  }, [videoId]);

  usePlayerTime(playerRef, isReady, onTimeUpdate);

  return (
    <div className="aspect-video w-full overflow-hidden rounded-xl bg-ink-900">
      <div ref={containerRef} className="h-full w-full" />
    </div>
  );
}
