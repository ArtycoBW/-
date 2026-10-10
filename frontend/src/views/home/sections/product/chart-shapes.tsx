import { useId } from "react";

/**
 * The bar chart's cube bodies and diamond caps as inline markup — the Figma
 * group exports (`public/assets/product/product-cube-*.svg`, `product-cap-*.svg`,
 * `product-cap-glow.svg`) drawn in place, path for path.
 *
 * As thirteen lazy `<img>`s they arrived while the page was being scrolled, and
 * each one built its own SVG document on the main thread in the frame that
 * revealed the chart — the scroll test's reproducible 76 ms frame at "Most of a
 * process is glue." on a phone (D-031). Inline, they are part of the server HTML
 * and paint with the card. Colours are the section's tokens (`product.css`).
 */

type Tone = "dim" | "accent";

/** `useId` output made safe inside `url(#…)`. */
const useSvgId = () => useId().replace(/[^A-Za-z0-9_-]/g, "");

const FACES = ["left", "right", "top"] as const;

/** One cube body, 76 wide and `h` tall in the export's own units; stretched to its box. */
export const ChartCube = ({ h, tone }: { h: number; tone: Tone }) => {
  const id = useSvgId();
  const grad = (face: (typeof FACES)[number]) => `${id}-${face}`;
  const stops = (face: (typeof FACES)[number]) => (
    <>
      <stop style={{ stopColor: `var(--product-cube-${tone}-${face}-from)` }} />
      <stop
        offset="1"
        style={{ stopColor: `var(--product-cube-${tone}-${face}-to)` }}
      />
    </>
  );
  return (
    <svg
      aria-hidden="true"
      viewBox={`0 0 76 ${h}`}
      preserveAspectRatio="none"
      fill="none"
      className="block size-full max-w-none"
    >
      <path d={`M0 48L38 68V${h}L0 ${h - 20}V48Z`} fill={`url(#${grad("left")})`} />
      <path d={`M38 68L76 48V${h - 20}L38 ${h}V68Z`} fill={`url(#${grad("right")})`} />
      <path d="M38 28L76 48L38 68L0 48L38 28Z" fill={`url(#${grad("top")})`} />
      <defs>
        <linearGradient id={grad("left")} x1="19" y1="48" x2="19" y2={h} gradientUnits="userSpaceOnUse">
          {stops("left")}
        </linearGradient>
        <linearGradient id={grad("right")} x1="57" y1="48" x2="57" y2={h} gradientUnits="userSpaceOnUse">
          {stops("right")}
        </linearGradient>
        <linearGradient id={grad("top")} x1="38" y1="28" x2="38" y2="68" gradientUnits="userSpaceOnUse">
          {stops("top")}
        </linearGradient>
      </defs>
    </svg>
  );
};

/** A diamond cap, 60 × 32. */
export const ChartCap = ({ tone, className }: { tone: Tone; className: string }) => (
  <svg aria-hidden="true" viewBox="0 0 60 32" fill="none" className={className}>
    <path
      d="M30 0L60 16L30 32L0 16L30 0Z"
      style={{ fill: `var(--product-cap-${tone})` }}
    />
  </svg>
);

/** The landed accent cap's glow, 100 × 72. */
export const ChartCapGlow = ({ className }: { className: string }) => {
  const id = `glow${useSvgId()}`;
  return (
    <svg aria-hidden="true" viewBox="0 0 100 72" fill="none" className={className}>
      <g filter={`url(#${id})`}>
        <path
          d="M50 20L80 36L50 52L20 36L50 20Z"
          style={{ fill: "var(--product-cap-accent)" }}
        />
      </g>
      <defs>
        <filter
          id={id}
          x="0"
          y="0"
          width="100"
          height="72"
          filterUnits="userSpaceOnUse"
          colorInterpolationFilters="sRGB"
        >
          <feGaussianBlur stdDeviation="8" />
        </filter>
      </defs>
    </svg>
  );
};
