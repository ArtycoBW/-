"use client";

import { useEffect } from "react";

/**
 * Route-segment error boundary. Must be a Client Component. Catches render and
 * data errors in this segment and offers a recovery action via `reset()`.
 */
export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Surface the error for logging/monitoring (kept by removeConsole's exclude).
    console.error(error);
  }, [error]);

  return (
    <div className="rz-loading">
      <h1 className="text-3xl font-bold">Не удалось открыть страницу</h1>
      <button
        type="button"
        onClick={reset}
        className="underline underline-offset-4"
      >
        Попробовать снова
      </button>
    </div>
  );
}
