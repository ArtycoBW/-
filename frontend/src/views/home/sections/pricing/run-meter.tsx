"use client";
import Link from "next/link";
import { animated, useSpring } from "@react-spring/web";
import type { PricingContent } from "@/data/mocks/home/pricing";
import { SPRING_SOFT } from "@/lib/motion";
export const INITIAL = 1;
export const planIndex = (pos: number, _tiers: PricingContent["tiers"]) =>
  Math.max(0, Math.min(2, Math.round(pos)));
export function RunMeter({
  meter,
  tiers,
  pos,
  onPos,
}: {
  meter: PricingContent["meter"];
  tiers: PricingContent["tiers"];
  pos: number;
  onPos: (p: number) => void;
}) {
  const tier = tiers[planIndex(pos, tiers)];
  const glow = useSpring({
    opacity: 1,
    from: { opacity: 0.3 },
    config: SPRING_SOFT,
  });
  return (
    <div className="razryad-role-picker">
      <div>
        <p>{meter.eyebrow} / ЛЦТ 2026</p>
        <h3>{meter.question}</h3>
        <div role="group" aria-label="Выберите роль">
          {tiers.map((t, i) => (
            <button
              key={t.name}
              aria-pressed={pos === i}
              onClick={() => onPos(i)}
            >
              {t.name}
            </button>
          ))}
        </div>
        <small>
          Доступ к прототипу бесплатный. Все стартовые профили — синтетические.
        </small>
      </div>
      <animated.div style={glow} className="razryad-role-result">
        <span>{tier.price}</span>
        <h3>{tier.name}</h3>
        <p>{tier.period}</p>
        <Link href={tier.cta.href}>{tier.cta.label} ↗</Link>
      </animated.div>
    </div>
  );
}
