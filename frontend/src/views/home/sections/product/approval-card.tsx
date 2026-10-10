"use client";

import { animated, useSpring, useSprings } from "@react-spring/web";
import Image from "next/image";
import { useEffect, useState } from "react";

import type { ProductContent } from "@/data/mocks/home/product";
import { SPRING, STEP } from "@/lib/motion";

import { CARD } from "./feature-row";
import { CARD_START } from "./use-card-play";
import { useLoopCycle } from "./use-loop-cycle";

/** Timeline, ms after the card enters view. */
const AT = {
  typing: CARD_START,
  typingOut: CARD_START + 880,
  message: CARD_START + 920,
  fields: CARD_START + 1120,
  fieldStep: 1.6 * STEP,
  bar: CARD_START + 1120 + 3.2 * STEP,
  /** Approve, Hold, then the waiting time — one STEP apart. */
  buttons: CARD_START + 1560,
} as const;
/** "waiting 26 min" gains a minute this often once the buttons are up. */
const TICK_MS = 720;
/** Ticks stop here so the hold keeps a steady value. */
const MAX_TICKS = 4;
const TICK_AT = AT.buttons + 1.6 * STEP + 400;
/** Play length: typing → buttons, then a few visible ticks. */
const PLAY_MS = TICK_AT + 3 * TICK_MS;

const RISE_FROM = { opacity: 0, y: 8 };
const RISE_TO = { opacity: 1, y: 0 };

/**
 * Row 02 Slack card — "Сообщение приходит" (motion brief, product.approval):
 * typing dots → Relay's message → fields line by line → accent bar grows down →
 * Approve / Hold rise → the waiting time ticks while in view.
 */
export const ApprovalCard = ({
  approval,
}: Pick<ProductContent, "approval">) => {
  const { ref, on, reduced, snap } = useLoopCycle(PLAY_MS);
  const [extraMinutes, setExtraMinutes] = useState(0);
  /** Reverse order on reset: later elements leave first. */
  const out = (rank: number) => rank * 32;

  const [message] = useSpring(
    () => ({
      from: RISE_FROM,
      to: on ? RISE_TO : RISE_FROM,
      delay: on ? AT.message : out(6),
      config: SPRING,
      immediate: snap,
    }),
    [on, snap],
  );
  const [fields] = useSprings(
    approval.fields.length,
    (i) => ({
      from: RISE_FROM,
      to: on ? RISE_TO : RISE_FROM,
      delay: on ? AT.fields + i * AT.fieldStep : out(5 - i),
      config: SPRING,
      immediate: snap,
    }),
    [on, snap],
  );
  const [buttons] = useSprings(
    3,
    (i) => ({
      from: RISE_FROM,
      to: on ? RISE_TO : RISE_FROM,
      delay: on ? AT.buttons + i * 0.8 * STEP : out(2 - i),
      config: SPRING,
      immediate: snap,
    }),
    [on, snap],
  );

  // Waiting clock: +1 min every TICK_MS once the buttons are up; back to the
  // Figma value while the card resets.
  useEffect(() => {
    if (reduced) return;
    if (!on) {
      const back = window.setTimeout(() => setExtraMinutes(0), 280);
      return () => window.clearTimeout(back);
    }
    let tick = 0;
    const start = window.setTimeout(() => {
      tick = window.setInterval(
        () => setExtraMinutes((m) => Math.min(MAX_TICKS, m + 1)),
        TICK_MS,
      );
    }, TICK_AT);
    return () => {
      window.clearTimeout(start);
      window.clearInterval(tick);
    };
  }, [on, reduced]);

  const waiting = approval.waiting.replace(/\d+/, (m) =>
    String(Number(m) + extraMinutes),
  );

  return (
    <figure ref={ref} className={`${CARD} rz-landing-invitation`}>
      <header><strong>{approval.channel}</strong><span>{approval.day}</span></header>
      <animated.div style={message} className="rz-offer-sender">
        <Image src="/brand/mark.svg" alt="" width={28} height={28} />
        <strong>{approval.sender}</strong><time>{approval.time}</time>
      </animated.div>
      <animated.p style={message} className="rz-offer-copy">{approval.message}</animated.p>
      <dl className="rz-offer-fields">
        {approval.fields.map((field, i) => (
          <animated.div key={field.key} style={fields[i]}><dt>{field.key}</dt><dd>{field.value}</dd></animated.div>
        ))}
      </dl>
      <div className="rz-offer-actions">
        <animated.span style={buttons[0]} className="rz-offer-accept">✓ {approval.approve}</animated.span>
        <animated.span style={buttons[1]} className="rz-offer-later">Ⅱ {approval.hold}</animated.span>
        <animated.p style={buttons[2]}>{waiting}</animated.p>
      </div>
    </figure>
  );
};
