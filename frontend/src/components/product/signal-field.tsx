"use client";
import { useEffect, useRef } from "react";

/** A small, dependency-free signal field. Stops offscreen and honours reduced motion. */
export function SignalField() {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = ref.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) return;
    const reduced = matchMedia("(prefers-reduced-motion: reduce)");
    let width = 0, height = 0, frame = 0, visible = true, previous = 0;
    const resize = () => {
      const box = canvas.getBoundingClientRect();
      width = box.width; height = box.height;
      const dpr = Math.min(devicePixelRatio, 1.5);
      canvas.width = width * dpr; canvas.height = height * dpr;
      context.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    const draw = (now: number) => {
      if (!visible || document.hidden) { frame = 0; return; }
      const t = reduced.matches ? 0 : now / 18000;
      if (now - previous > 32 || reduced.matches) {
        previous = now;
        context.clearRect(0, 0, width, height);
        for (let line = 0; line < 46; line++) {
          const offset = line / 46;
          context.beginPath();
          for (let step = 0; step <= 88; step++) {
            const x = step / 88 * width;
            const angle = step / 88 * 5.4 + offset * 1.25 + t;
            const y = height * (.5 + Math.sin(angle) * .23) + (offset - .5) * height * .35;
            if (step === 0) context.moveTo(x, y); else context.lineTo(x, y);
          }
          context.strokeStyle = `rgba(183,160,255,${.07 + Math.sin(offset * Math.PI) * .2})`;
          context.lineWidth = line % 8 === 0 ? 1.2 : .6;
          context.stroke();
          const progress = (t * .6 + offset * 2.7) % 1;
          const x = progress * width;
          const y = height * (.5 + Math.sin(progress * 5.4 + offset * 1.25 + t) * .23) + (offset - .5) * height * .35;
          context.fillStyle = `rgba(225,216,255,${.25 + offset * .5})`;
          context.beginPath(); context.arc(x, y, line % 5 === 0 ? 2 : 1, 0, Math.PI * 2); context.fill();
        }
      }
      frame = reduced.matches ? 0 : requestAnimationFrame(draw);
    };
    const start = () => { if (!frame && visible && !document.hidden) frame = requestAnimationFrame(draw); };
    const observer = new ResizeObserver(() => { resize(); start(); });
    observer.observe(canvas);
    const intersection = new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; start(); });
    intersection.observe(canvas);
    document.addEventListener("visibilitychange", start);
    reduced.addEventListener("change", start);
    resize(); start();
    return () => { cancelAnimationFrame(frame); observer.disconnect(); intersection.disconnect(); document.removeEventListener("visibilitychange", start); reduced.removeEventListener("change", start); };
  }, []);
  return <canvas className="rz-signal-field" ref={ref} aria-hidden="true" />;
}
