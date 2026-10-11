"use client";
import { useEffect, useRef } from "react";

export function PracticeScene() {
  const canvas = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const motion = matchMedia("(prefers-reduced-motion: reduce)");
    let stopped = false;
    let dispose: (() => void) | undefined;
    async function start() {
      dispose?.();
      dispose = undefined;
      if (motion.matches || stopped || !canvas.current) return;
      try {
        const { mountPracticeGrid } = await import("./practice-grid.js");
        if (!stopped && !motion.matches && canvas.current)
          dispose = mountPracticeGrid(canvas.current);
      } catch {
        /* Статическая сетка остаётся доступной без WebGL. */
      }
    }
    void start();
    motion.addEventListener("change", start);
    return () => {
      stopped = true;
      motion.removeEventListener("change", start);
      dispose?.();
    };
  }, []);
  return (
    <div className="rz-practice-scene" aria-hidden="true">
      <canvas ref={canvas} />
    </div>
  );
}
