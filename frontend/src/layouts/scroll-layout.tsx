"use client";

import { useEffect, useRef, useState } from "react";
import Lenis from "lenis";
import { usePathname } from "next/navigation";
import { useScroll } from "@/hooks/smooth-scroll/use-scroll";
import { scrollTo } from "@/utils/scroll-to";
import { useShallow } from "zustand/react/shallow";

export const scrollSpeed = { current: 1 };

export function ScrollLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  // Плавный скролл нужен только на лендинге.
  return (
    <div className="scroll-layout">
      {/* Static content that can be rendered on server */}
      <div className="scroll-layout-content">{children}</div>

      {/* Client-only functionality */}
      {pathname === "/" && <ScrollController />}
    </div>
  );
}

function ScrollController() {
  const isEnableScroll = useScroll((state) => state.isEnableScroll);
  const [hash, setHash] = useState<string>("");
  const [lenis, setLenis] = useScroll(
    useShallow((state) => [state.lenis, state.setLenis]),
  );
  const pathname = usePathname();
  const savedPathname = useRef("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.scrollTo(0, 0);
    const lenis = new Lenis({
      smoothWheel: true,
      // syncTouch: true,
    });
    (window as typeof window & { lenis: Lenis }).lenis = lenis;
    setLenis(lenis);

    let rafId = 0;
    const raf = (time: number) => {
      lenis.raf(time);
      rafId = requestAnimationFrame(raf);
    };
    rafId = requestAnimationFrame(raf);

    // Lenis measures the page's scroll limit itself and re-measures only when
    // the <html> box resizes. The home preloader holds <main> off-screen
    // (html[data-preload]), which adds overflow without changing any box —
    // so Lenis kept a limit ~2 viewports past the real end and the wheel ran
    // on past the footer ("stuck", then dead scrolls back up). Re-measure
    // whenever those flags change, and once the fonts have settled.
    //
    // The preloader also holds the scroll. `overflow: hidden` on <html> stops
    // the browser, but not Lenis: it scrolls the window itself, so a wheel or
    // trackpad flick under the lime stage ran the page ~1,600 px down (into
    // the room `<main>` takes while it waits off-screen), and the fold then
    // uncovered the page sections down instead of the hero. So Lenis stops
    // while the stage is up — and through its fold (`data-preload-closing`),
    // so what the fold uncovers is always the hero — and when it is gone the
    // page is put back at the very top before scrolling comes back, whatever
    // moved it meanwhile (a restored position, a phone's native touch scroll).
    const root = document.documentElement;
    let held = false;
    const remeasure = () => {
      const hold = "preload" in root.dataset || "preloadClosing" in root.dataset;
      if (hold && !held) {
        held = true;
        lenis.stop();
      } else if (!hold && held) {
        held = false;
        window.scrollTo(0, 0);
        lenis.scrollTo(0, { immediate: true, force: true });
        if (useScroll.getState().isEnableScroll) lenis.start();
      }
      lenis.resize();
    };
    remeasure();
    const flags = new MutationObserver(remeasure);
    flags.observe(document.documentElement, {
      attributeFilter: ["data-preload", "data-preload-closing"],
    });
    document.fonts.ready.then(remeasure);

    return () => {
      // Cancel the loop before destroying Lenis — otherwise it keeps calling
      // `raf` on a destroyed instance after unmount/HMR.
      cancelAnimationFrame(rafId);
      flags.disconnect();
      lenis.destroy();
      setLenis(null);
    };
  }, [setLenis]);

  useEffect(() => {
    if (isEnableScroll) {
      // not while the preloader holds the page (see the hold above)
      const { dataset } = document.documentElement;
      if (!("preload" in dataset || "preloadClosing" in dataset)) lenis?.start();
      enableNativeScroll(true);
    } else {
      lenis?.stop();
      enableNativeScroll(false);
    }
  }, [isEnableScroll, lenis]);

  useEffect(() => {
    if (lenis && hash) {
      setTimeout(() => {
        scrollTo(hash, true);
      }, 300);
    }
  }, [lenis, hash]);

  useEffect(() => {
    if (savedPathname.current !== pathname) {
      savedPathname.current = pathname;
      if (pathname.includes("#")) {
        const hash = pathname.split("#").pop();
        if (hash) {
          setHash(hash);
        }
      }
    }
  }, [pathname, setHash]);

  return null; // This component doesn't render anything visible
}

const enableNativeScroll = (value: boolean) => {
  if (typeof document === "undefined") return;
  if (!document) return;
  const html = document.querySelector("html");
  if (!html) return;
  if (!value) {
    html.style.position = "relative";
    html.style.overflow = "hidden";
    html.style.height = "100%";
  } else {
    html.style.removeProperty("position");
    html.style.removeProperty("overflow");
    html.style.removeProperty("height");
  }
};
