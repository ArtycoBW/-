"use client";

import { use, type ReactNode } from "react";

/**
 * Hydrate a server-rendered block only once the visitor nears it.
 *
 * Every block below the hero sits in its own `<Suspense>` (ADR-0028). Put this
 * inside one, around the block, and the block's hydration waits: the component
 * suspends while React hydrates, and React keeps the server HTML in place for
 * a boundary that suspends during hydration — then hydrates it, in place (no
 * remount, nothing re-created), once the gate opens. Hydrating every block at
 * once was the page's one long task at load: a few hundred reveals starting
 * their springs in a single commit (mobile TBT ~0.5 s at 4× CPU).
 *
 * The gate opens when the block (`id`) is on screen — or, from the visitor's
 * first gesture toward moving the page, within 1.5 viewports of it. Before
 * that gesture nothing below the hero can come near: the page opens at the
 * top, held off-screen under the preloader until the fold. `scroll` also
 * counts as that gesture, so a restored or hash-anchored position opens the
 * gates around it.
 *
 * On the server, and on a client render that is not hydration (a navigation
 * back to the page), the block renders at once: the element is not in the
 * document yet, so its gate is open. The robot form (D-016) goes through the
 * same gate — its served HTML already holds every block at rest.
 */
const LOOKAHEAD = "150% 0px 150% 0px";
const ENGAGE_EVENTS = ["pointerdown", "touchstart", "wheel", "keydown", "scroll"] as const;

let engaged = false;
const engageWaiters = new Set<() => void>();
const engage = () => {
  if (engaged) return;
  engaged = true;
  for (const type of ENGAGE_EVENTS) window.removeEventListener(type, engage, true);
  for (const wake of engageWaiters) wake();
  engageWaiters.clear();
};
const onEngaged = (wake: () => void) => {
  if (engaged) {
    wake();
    return;
  }
  if (engageWaiters.size === 0) {
    for (const type of ENGAGE_EVENTS) {
      window.addEventListener(type, engage, { capture: true, passive: true });
    }
  }
  engageWaiters.add(wake);
};

/**
 * A desktop behind the preloader does not wait for the approach: its blocks
 * hydrate one per idle moment, in page order, from the first screen's
 * hydration on — under the preloader, where the main thread mostly waits on
 * the network. Hydrated on approach, the first wheel opened every gate within
 * 1.5 viewports at once and their 25–60 ms tasks landed on the first scroll
 * (owner review: "on pc the first scroll there are so many freezes"). Phones,
 * the robot form and reduced motion (no preloader) keep the approach gate:
 * on a phone the same work at load is TBT.
 */
const DESKTOP = "(hover: hover) and (pointer: fine) and (min-width: 901px)";
const queue: Array<() => void> = [];
let idle: "off" | "waiting" | "running" = "off";
const pump = () => {
  idle = "running";
  const open = queue.shift();
  if (!open) {
    idle = "waiting";
    return;
  }
  open();
  if (typeof window.requestIdleCallback === "function")
    window.requestIdleCallback(pump, { timeout: 1500 });
  else window.setTimeout(pump, 50);
};
const enqueue = (open: () => void) => {
  if (idle === "off") {
    const root = document.documentElement;
    if (!("preload" in root.dataset) || !window.matchMedia(DESKTOP).matches)
      return;
    idle = "waiting";
  }
  queue.push(open);
  if (idle === "waiting") {
    idle = "running";
    if (typeof window.requestIdleCallback === "function")
      window.requestIdleCallback(pump, { timeout: 1500 });
    else window.setTimeout(pump, 50);
  }
};

const gates = new Map<string, Promise<void>>();

const gateFor = (id: string): Promise<void> => {
  const known = gates.get(id);
  if (known) return known;
  const gate = new Promise<void>((open) => {
    const el = document.getElementById(id);
    if (!el) {
      open();
      return;
    }
    let io: IntersectionObserver | null = null;
    let done = false;
    const release = () => {
      if (done) return;
      done = true;
      io?.disconnect();
      open();
    };
    const watch = (rootMargin: string) => {
      if (done) return;
      io?.disconnect();
      io = new IntersectionObserver(
        (entries) => {
          if (entries.some((entry) => entry.isIntersecting)) release();
        },
        { rootMargin },
      );
      io.observe(el);
    };
    watch("0px");
    onEngaged(() => watch(LOOKAHEAD));
    enqueue(release);
  });
  gates.set(id, gate);
  return gate;
};

export const HydrateNear = ({
  id,
  children,
}: {
  /** The block's root element id — what the gate watches. */
  id: string;
  children: ReactNode;
}) => {
  if (typeof window !== "undefined") use(gateFor(id));
  return children;
};
