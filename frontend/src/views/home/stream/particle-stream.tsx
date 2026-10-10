"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";

import { useFrame } from "@/hooks/use-frame";
import { useSeen } from "@/hooks/use-seen";
import { subscribeToTicker } from "@/lib/animation/ticker";
import { readScrollY } from "@/lib/scroll-y";
import { isBotClient } from "@/utils/bot-ua";
import {
  getStableViewportHeight,
  subscribeStableViewport,
} from "@/utils/stable-viewport";
import { LOAD } from "@/views/home/sections/hero/timeline";

import { PATH, resolvePath } from "./stream-path";
import type { StreamColors, StreamScene, Tier } from "./stream-scene";

const COARSE = "(hover: none) and (pointer: coarse)";
const FINE = "(hover: hover) and (pointer: fine)";
const REDUCE = "(prefers-reduced-motion: reduce)";
/** The frame reduced motion shows: the stream fully drawn, frozen mid-flow. */
const STILL_MS = 24000;
/**
 * Frame budget: none — the stream draws on every display frame everywhere.
 * A phone cap (a 20 ms gap: 30 fps at 60 Hz, 40 at 120 Hz) read as a choppy
 * stream while scrolling (owner review 3, D-037); the phone pays with the low
 * tier's cheaper frame instead (./stream-scene `DPR`, `lowShare`, bloom scale).
 */
const NO_GAP = () => 0;
/** Before the first measure (server render, first paint): the CSS `h-lvh`. */
const serverHeight = () => 0;

const readTier = (): Tier =>
  window.matchMedia(COARSE).matches || window.innerWidth <= 900
    ? "low"
    : "full";

const PRELOAD_FLAGS = ["data-preload", "data-preload-closing"];

/** Hand the main thread back between build steps (idle time when there is any). */
const yieldToMain = () =>
  new Promise<void>((resolve) => {
    if (typeof window.requestIdleCallback === "function")
      window.requestIdleCallback(() => resolve(), { timeout: 800 });
    else window.setTimeout(resolve, 0);
  });

/**
 * `true` once the home preloader has fully closed (or never ran). The stream
 * neither renders nor starts its entrance before then — its bloom sharing the
 * GPU with the preloader's fold made the fold stutter.
 */
const usePreloaderGone = () => {
  const [gone, setGone] = useState(false);
  useEffect(() => {
    const root = document.documentElement;
    const read = () =>
      setGone(!("preload" in root.dataset || "preloadClosing" in root.dataset));
    read();
    const watch = new MutationObserver(read);
    watch.observe(root, { attributeFilter: PRELOAD_FLAGS });
    return () => watch.disconnect();
  }, []);
  return gone;
};

/**
 * When the stream may start building. Everywhere: once the preloader has gone.
 * On a desktop (full tier, fine pointer), already at `load` — under the
 * preloader's last beat (the ring closing, the flood), in short steps, so the
 * scene is compiled and warm before the visitor can scroll; built after the
 * fold, it landed on the first scroll (owner review: "the first scroll there
 * are so many freezes"). It still neither renders nor reveals before the
 * preloader has gone. Phones keep the late build: their load is the bottleneck.
 */
const useBuildGate = (live: boolean) => {
  const [early, setEarly] = useState(false);
  useEffect(() => {
    if (readTier() !== "full" || !window.matchMedia(FINE).matches) return;
    if (document.readyState === "complete") {
      setEarly(true);
      return;
    }
    const onLoad = () => setEarly(true);
    window.addEventListener("load", onLoad, { once: true });
    return () => window.removeEventListener("load", onLoad);
  }, []);
  return live || early;
};

/** The four colour roles come from the `--stream-*` tokens. */
const readColors = (el: Element): StreamColors => {
  const style = getComputedStyle(el);
  const token = (name: string) => style.getPropertyValue(name).trim();
  return {
    colMain: token("--stream-main"),
    colAlt: token("--stream-alt"),
    colCore: token("--stream-core"),
    colDeep: token("--stream-deep"),
    colSpark: token("--stream-spark"),
  };
};

/**
 * The lime 3D particle stream under the whole page (./stream-scene). The
 * canvas is fixed to the viewport, above the backdrop and under every
 * section; the stream itself is laid out in page coordinates (./stream-path)
 * and scrolls with the page. Opaque black blended with `screen`, so black
 * adds nothing and the bloom glows over the backdrop without an alpha pass;
 * glass surfaces (the hero window, the Product → Proof slab) frost it.
 *
 * three.js loads on demand after hydration — never for a crawler or a lab
 * run (bot-ua), which get the page without it. The scene is built in steps
 * with the main thread handed back between them (chunk, geometry, shader
 * compile through KHR_parallel_shader_compile, first frame), so no single
 * task is long enough to stall the preloader's ring; it then draws itself
 * in down its curve with the hero's load sequence (LOAD.stream after the
 * page is seen). The path re-resolves whenever the page's layout changes
 * size. Renders through the shared ticker on every frame while the tab is
 * visible (no phone cap — see NO_GAP); scrolling also pushes the flow on down
 * the curve, so it never reads as climbing while the page moves up. The
 * pointer gives a small camera parallax on fine pointers only. Reduced
 * motion gets a still frame, redrawn on scroll. Nothing renders, and the
 * entrance waits, until the preloader has fully closed. The canvas is the
 * large viewport tall (`lvh`, then a px height measured once and, on a touch
 * device, re-measured only when the width changes — utils/stable-viewport),
 * so a phone's URL bar collapsing or expanding with the scroll direction
 * never resizes the canvas, re-allocates the framebuffer or rescales the
 * stream (owner review 3, D-037). The box is CSS px, never rem, so the
 * phones' root-font scaling does not reach it.
 * Its look lives in `CONFIG` (./stream-scene).
 */
export const ParticleStream = () => {
  const ref = useRef<HTMLCanvasElement>(null);
  const sceneRef = useRef<StreamScene | null>(null);
  const [ready, setReady] = useState(false);
  const frame = useFrame();
  const seen = useSeen(ref);
  const live = usePreloaderGone();
  const buildable = useBuildGate(live);
  const boxHeight = useSyncExternalStore(
    subscribeStableViewport,
    getStableViewportHeight,
    serverHeight,
  );

  // create on demand, in steps, dispose on unmount — once the preloader has
  // gone (a desktop: from `load`, see useBuildGate): fetched and built under
  // it, three (141 KB) and the build were billed to the first screen's paint,
  // which the preloader gates (optimize-load §LCP)
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || !buildable || isBotClient()) return;
    let alive = true;
    let scene: StreamScene | null = null;
    const build = async () => {
      const { StreamScene } = await import("./stream-scene");
      if (!alive) return;
      await yieldToMain();
      if (!alive) return;
      try {
        scene = new StreamScene(canvas, readColors(canvas));
      } catch {
        return; // no WebGL — the page stands without the stream
      }
      await yieldToMain();
      if (!alive) return;
      scene.retune(readTier());
      scene.resize(canvas.clientWidth, canvas.clientHeight);
      scene.setScroll(window.scrollY);
      await scene.prewarm(yieldToMain);
      if (!alive) return;
      sceneRef.current = scene;
      setReady(true);
    };
    void build();
    return () => {
      alive = false;
      scene?.dispose();
      sceneRef.current = null;
    };
  }, [buildable]);

  // the path follows the page: re-resolve on any layout size change
  useEffect(() => {
    const canvas = ref.current;
    const scene = sceneRef.current;
    const main = canvas?.closest("main");
    if (!ready || !scene || !main) return;
    let raf = 0;
    const place = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        scene.setPath(resolvePath(PATH[frame], main));
        if (window.matchMedia(REDUCE).matches) scene.render(STILL_MS);
      });
    };
    place();
    const layout = new ResizeObserver(place);
    layout.observe(main);
    return () => {
      cancelAnimationFrame(raf);
      layout.disconnect();
    };
  }, [ready, frame]);

  // viewport size, device tier (re-read on any width change or pointer flip),
  // pointer, and the loop
  useEffect(() => {
    const canvas = ref.current;
    const scene = sceneRef.current;
    if (!ready || !scene || !canvas) return;
    const reduce = window.matchMedia(REDUCE);
    const coarse = window.matchMedia(COARSE);
    const fine = window.matchMedia(FINE);
    let tier = readTier();
    let stop: (() => void) | null = null;
    let raf = 0;
    let width = canvas.clientWidth;
    let height = canvas.clientHeight;

    const still = () => {
      scene.setScroll(window.scrollY);
      scene.reveal(STILL_MS, true);
      scene.render(STILL_MS);
    };
    const sync = () => {
      const run = live && !document.hidden && !reduce.matches;
      if (run && !stop) {
        stop = subscribeToTicker((time) => {
          scene.setScroll(readScrollY());
          scene.render(time);
        }, NO_GAP);
      } else if (!run && stop) {
        stop();
        stop = null;
      }
      if (reduce.matches) still();
    };
    // reduced motion: no loop, so a scroll redraws the still frame directly
    const onScroll = () => {
      if (!reduce.matches) return;
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(still);
    };
    const onResize = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const next = readTier();
        const w = canvas.clientWidth;
        const h = canvas.clientHeight;
        // the canvas box is locked to the large viewport (stable-viewport), so
        // a phone's URL bar leaves it as it is; a real change (rotation, a
        // breakpoint drag, emulation off) retunes
        if (next === tier && w === width && h === height) return;
        width = w;
        height = h;
        if (next !== tier) {
          tier = next;
          scene.retune(tier);
        }
        scene.resize(w, h);
        if (reduce.matches) still();
      });
    };
    const onPointer = (e: PointerEvent) => {
      if (reduce.matches || e.pointerType !== "mouse") return;
      scene.setPointer(
        (e.clientX / window.innerWidth) * 2 - 1,
        (e.clientY / window.innerHeight) * 2 - 1,
      );
    };

    sync();
    window.addEventListener("resize", onResize);
    // a rotation settles the locked height a beat after its resize event
    const unlock = subscribeStableViewport(onResize);
    window.addEventListener("scroll", onScroll, { passive: true });
    // no pointer work at all where there is no fine pointer
    if (fine.matches)
      window.addEventListener("pointermove", onPointer, { passive: true });
    coarse.addEventListener("change", onResize);
    reduce.addEventListener("change", sync);
    document.addEventListener("visibilitychange", sync);
    return () => {
      stop?.();
      cancelAnimationFrame(raf);
      unlock();
      window.removeEventListener("resize", onResize);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("pointermove", onPointer);
      coarse.removeEventListener("change", onResize);
      reduce.removeEventListener("change", sync);
      document.removeEventListener("visibilitychange", sync);
    };
  }, [ready, live]);

  // entrance with the hero's load sequence
  useEffect(() => {
    const scene = sceneRef.current;
    if (!ready || !seen || !live || !scene) return;
    if (window.matchMedia(REDUCE).matches) return;
    const timer = window.setTimeout(
      () => scene.reveal(performance.now()),
      LOAD.stream,
    );
    return () => window.clearTimeout(timer);
  }, [ready, seen, live]);

  return (
    <canvas
      ref={ref}
      aria-hidden
      className="pointer-events-none fixed top-0 left-0 h-lvh w-full mix-blend-screen"
      style={boxHeight > 0 ? { height: boxHeight } : undefined}
    />
  );
};
