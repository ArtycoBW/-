"use client";

import { animated, useSpring, useTrail, type SpringValue } from "@react-spring/web";
import Image from "next/image";
import Link from "next/link";
import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  useSyncExternalStore,
  type MouseEvent,
} from "react";
import { createPortal } from "react-dom";

import { SessionNavButton } from "@/components/product/session-navigation";
import type { NavContent } from "@/data/mocks/home/nav";
import { useScroll } from "@/hooks/smooth-scroll/use-scroll";
import { useFrame } from "@/hooks/use-frame";
import { SPRING } from "@/lib/motion";

import { BreathingDot } from "./breathing-dot";

/** The exit is the entrance reversed, quicker — a menu leaves faster than it arrives. */
const SPRING_OUT = { tension: 420, friction: 40 } as const;
/** Link rows trail in this far apart, ms. */
const ROW_STEP = 50;

const REDUCE = "(prefers-reduced-motion: reduce)";
const noop = () => () => {};

/** The burger's three bars fold into a cross as `t` runs 0 → 1. */
const Bars = ({ t }: { t: SpringValue<number> }) => (
  <>
    <animated.span
      aria-hidden="true"
      className="absolute top-3.25 left-2.75 h-0.5 w-4 rounded-full bg-foreground/90"
      style={{
        transform: t.to((v) => `translateY(${v * 0.375}rem) rotate(${v * 45}deg)`),
      }}
    />
    <animated.span
      aria-hidden="true"
      className="absolute top-4.75 left-2.75 h-0.5 w-4 rounded-full bg-foreground/90"
      style={{ opacity: t.to((v) => 1 - v) }}
    />
    <animated.span
      aria-hidden="true"
      className="absolute top-6 left-3.5 h-0.5 w-2.5 rounded-full bg-foreground/90"
      style={{
        transform: t.to(
          (v) =>
            `translateY(${-v * 0.3125}rem) rotate(${-v * 45}deg) scaleX(${1 + v * 0.6})`,
        ),
      }}
    />
  </>
);

type Origin = { x: number; y: number; r: number };

/**
 * Menu button of the 390 frame (Menu 3900:3 — 40 round glass button with
 * three bars, the last one shorter) and the full-screen menu it opens (owner
 * review 2026-10-06 — it used to be a card grown out of the bar; not in Figma).
 *
 * The menu is a page-black sheet over everything (the particle stream, the
 * cookie banner), portalled to <body>: it opens as a circle growing out of the
 * button, its own bar (brand + the same button, now a cross) sitting exactly
 * where the nav's is; the links rise out of a mask one after another in large
 * type, with the status and the CTA at the bottom. The exit is the same
 * motion reversed, on a quicker spring. Reduced motion: a plain fade.
 *
 * While open the page does not scroll (the scroll store stops Lenis and the
 * native scroll), Escape closes, focus moves to the menu's button and is kept
 * inside, and comes back to the nav's button on close. A link closes the menu
 * and glides the page to its section. Closing, the sheet is `inert`; closed, unmounted.
 * Only reachable at 390 (`w390:`); it closes itself if the layout leaves it.
 */
export const NavMenu = ({
  brand,
  links,
  status,
  cta,
}: Pick<NavContent, "brand" | "links" | "status" | "cta">) => {
  const [open, setOpen] = useState(false);
  // mounted from the open until the exit has come to rest
  const [shown, setShown] = useState(false);
  const [origin, setOrigin] = useState<Origin | null>(null);
  const frame = useFrame();
  const panelId = useId();
  // the portal needs <body>: client only, after hydration
  const mounted = useSyncExternalStore(
    noop,
    () => true,
    () => false,
  );

  if (open && frame !== 390) setOpen(false);

  const toggle = useRef<HTMLButtonElement>(null);
  const sheet = useRef<HTMLDivElement>(null);
  const close = useRef<HTMLButtonElement>(null);
  /** Where focus goes after closing: back to the toggle unless a link took the visitor elsewhere. */
  const refocus = useRef(true);

  const reduce = useSyncExternalStore(
    (cb) => {
      const mq = window.matchMedia(REDUCE);
      mq.addEventListener("change", cb);
      return () => mq.removeEventListener("change", cb);
    },
    () => window.matchMedia(REDUCE).matches,
    () => false,
  );

  const openMenu = () => {
    const box = toggle.current?.getBoundingClientRect();
    if (box) {
      const x = box.left + box.width / 2;
      const y = box.top + box.height / 2;
      const w = window.innerWidth;
      const h = window.innerHeight;
      setOrigin({ x, y, r: Math.hypot(Math.max(x, w - x), Math.max(y, h - y)) });
    }
    refocus.current = true;
    setShown(true);
    setOpen(true);
  };

  const shut = useCallback(() => setOpen(false), []);

  // scroll lock, Escape, focus in and back out, focus kept inside
  useEffect(() => {
    if (!open) return;
    const { stop, start } = useScroll.getState();
    const opener = toggle.current;
    stop();
    close.current?.focus({ preventScroll: true });
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        shut();
        return;
      }
      if (e.key !== "Tab" || !sheet.current) return;
      const items = sheet.current.querySelectorAll<HTMLElement>("a[href], button");
      if (items.length === 0) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("keydown", onKey);
      start();
      if (refocus.current) opener?.focus({ preventScroll: true });
    };
  }, [open, shut]);

  const s = useSpring({
    t: open ? 1 : 0,
    config: open ? SPRING : SPRING_OUT,
    onRest: ({ value }) => {
      if (!open && value.t === 0) setShown(false);
    },
  });
  const rows = useTrail(links.length + 1, {
    t: open ? 1 : 0,
    delay: open ? 140 : 0,
    config: open ? SPRING : SPRING_OUT,
  });

  // A link (or the CTA) closes the menu and glides the page to its section.
  const onLink = (e: MouseEvent<HTMLElement>) => {
    const a = (e.target as HTMLElement).closest("a");
    const href = a?.getAttribute("href");
    if (!href?.startsWith("#")) return;
    e.preventDefault();
    refocus.current = false;
    shut();
    history.replaceState(null, "", href);
    const target = document.getElementById(href.slice(1));
    if (!target) return;
    // glide once the scroll lock has let go — Lenis restarting resets any
    // scroll begun while it was stopped
    const go = () => {
      const lenis = useScroll.getState().lenis;
      if (lenis?.isStopped) {
        requestAnimationFrame(go);
        return;
      }
      if (lenis) lenis.scrollTo(target, { duration: 1.2 });
      else target.scrollIntoView({ behavior: reduce ? "auto" : "smooth" });
    };
    requestAnimationFrame(go);
  };

  const clip = (t: number) =>
    reduce || !origin
      ? "none"
      : `circle(${t * origin.r}px at ${origin.x}px ${origin.y}px)`;

  return (
    <>
      <button
        ref={toggle}
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        aria-label="Открыть меню"
        onClick={openMenu}
        className="relative hidden size-10 shrink-0 cursor-pointer rounded-full border border-border-subtle bg-surface-glass w390:block"
      >
        <Bars t={s.t} />
      </button>

      {mounted &&
        shown &&
        createPortal(
          <animated.div
            ref={sheet}
            id={panelId}
            role="dialog"
            aria-modal="true"
            aria-label="Меню"
            inert={!open}
            onClick={onLink}
            className="fixed inset-0 z-90 hidden h-dvh flex-col bg-background font-sans w390:flex"
            style={{
              clipPath: s.t.to(clip),
              opacity: reduce ? s.t : 1,
            }}
          >
            {/* the nav bar again, in the same place: brand + the button as a cross */}
            <div className="flex h-14 shrink-0 items-center justify-between px-page-edge">
              <Link href={brand.href} className="flex items-center gap-3">
                <Image
                  src="/brand/mark.svg"
                  alt=""
                  width={28}
                  height={28}
                  className="size-7"
                />
                <span className="text-body leading-body font-medium tracking-wordmark text-foreground">
                  {brand.name}
                </span>
              </Link>
              <button
                ref={close}
                type="button"
                aria-label="Закрыть меню"
                onClick={shut}
                className="relative size-10 shrink-0 cursor-pointer rounded-full border border-border-subtle bg-surface-glass"
              >
                <Bars t={s.t} />
              </button>
            </div>

            <nav aria-label="Основная навигация" className="flex flex-1 flex-col justify-center px-page-edge">
              <ul className="flex flex-col">
                {links.map((link, i) => (
                  <li key={link.label} className="border-b border-border-subtle first:border-t">
                    <Link
                      href={link.href}
                      className="group flex items-baseline gap-4 py-4"
                    >
                      <animated.span
                        className="w-6 shrink-0 font-mono text-label leading-label text-foreground-dim transition-colors duration-(--motion-fast) ease-entrance group-hover:text-accent group-focus-visible:text-accent"
                        style={{ opacity: rows[i].t }}
                      >
                        {link.code}
                      </animated.span>
                      <span className="flex min-w-0 flex-col overflow-clip">
                        <animated.span
                          className="block text-menu-link leading-display font-medium tracking-title text-foreground transition-colors duration-(--motion-fast) ease-entrance group-hover:text-accent group-focus-visible:text-accent"
                          style={{
                            transform: rows[i].t.to(
                              (t) => `translateY(${(1 - t) * 105}%)`,
                            ),
                          }}
                        >
                          {link.label}
                        </animated.span>
                        <animated.span
                          className="text-label leading-label text-foreground-muted"
                          style={{ opacity: rows[i].t }}
                        >
                          {link.note}
                        </animated.span>
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>

            <animated.div
              className="flex shrink-0 items-center justify-between gap-3 px-page-edge pt-6 pb-[max(--spacing(6),env(safe-area-inset-bottom))]"
              style={{
                opacity: rows[links.length].t,
                transform: rows[links.length].t.to(
                  (t) => `translateY(${1 - t}rem)`,
                ),
              }}
            >
              <p className="flex h-11 items-center gap-2 overflow-clip rounded-full border border-border-glass bg-surface-status px-4">
                <BreathingDot />
                <span className="font-mono text-label leading-label whitespace-nowrap text-foreground">
                  {status}
                </span>
              </p>
              <SessionNavButton href={cta.href} size="lg">
                {cta.label}
              </SessionNavButton>
            </animated.div>
          </animated.div>,
          document.body,
        )}
    </>
  );
};
