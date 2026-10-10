import Image, { getImageProps } from "next/image";

const { props: dotField } = getImageProps({
  src: "/assets/backdrop/backdrop-dot-field.svg",
  alt: "",
  width: 1440,
  height: 1060,
  loading: "eager",
  fetchPriority: "high",
  decoding: "sync",
});
const { props: dotField768 } = getImageProps({
  src: "/assets/backdrop/backdrop-dot-field-768.svg",
  alt: "",
  width: 768,
  height: 1154,
});

/**
 * Page backdrop — the layers the frame paints behind the sections.
 *
 * - Top: Backdrop 3888:4242, 1440 × 1154 behind nav, hero and integrations —
 *   top light, dot field, specks and marks, base light, lime base line.
 * - Field texture 3888:2737, 1440 × 2400 at y=3781 — a 48 dot grid with
 *   four marks, behind 06 Scale onwards. Every frame squeezes it to its own
 *   width (`w-page`) at the same y.
 *
 * Positions are the frame's own coordinates; the parent is the page.
 *
 * 1024 (3888:8647): dot field and specks keep their 1440 width and run past
 * the frame (flat `w-360`); the base line sits at 1153 as at 1440.
 *
 * 768 (3832:5914) and 390 (3893:1508) share one 768-wide backdrop (at 390 it
 * simply runs past the frame): the dot field is re-pitched to 25.6 × 44.3 with
 * round 4 px dots (its own asset), the specks keep their x and are squeezed
 * to 12/13 of their height (1180 → 1089.2), the top light is 559 tall, the
 * base light peaks at 55% and fades out, and the base line sits at 1267
 * (390: 1220), under integrations.
 */
export const Backdrop = () => (
  <div aria-hidden className="pointer-events-none absolute inset-0">
    <div className="absolute inset-x-0 top-0 h-288.5">
      <div className="absolute top-0 right-[calc(50%-50vw)] left-[calc(50%-50vw)] h-140 bg-linear-to-b/srgb from-backdrop-light to-transparent w768:h-139.75" />
      {/* One dot field per breakpoint, as art direction: a phone fetches only
          its own (two `priority` images each fetched the one it hides). */}
      <picture>
        <source media="(max-width: 900px)" srcSet={dotField768.srcSet ?? dotField768.src} />
        <img
          {...dotField}
          alt=""
          className="absolute top-0 left-0 h-265 w-page max-w-none translate-y-[calc(var(--hero-extra)/2)] w1024:w-360 w768:h-288.5 w768:w-192"
        />
      </picture>
      <Image
        src="/assets/backdrop/backdrop-specks-and-marks.svg"
        alt=""
        width={1440}
        height={1180}
        className="absolute top-0 left-0 h-295 w-page max-w-none translate-y-[calc(var(--hero-extra)/2)] w1024:w-360 w768:h-[calc(var(--spacing)*272.3)]"
        priority
        fetchPriority="high"
        decoding="sync"
      />
      {/* at 1024 the base light + lime line close off 03 Integrations, which ends at 1012 */}
    </div>
    <Image
      src="/assets/backdrop/field-texture.svg"
      alt=""
      width={1440}
      height={2400}
      className="absolute top-945.25 left-0 h-600 w-page max-w-none translate-y-(--hero-extra) opacity-35"
    />
  </div>
);
