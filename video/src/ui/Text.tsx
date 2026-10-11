import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT, MARGIN, W } from "../brand";
import { clamp01, sp, SPRING } from "../lib/motion";
import type { Chunk } from "../lib/vo";

type Base = { delay?: number; style?: React.CSSProperties; children: React.ReactNode };

/** Headline that enters word by word (staggered springs), never letter-by-letter noise. */
export const Headline: React.FC<Base & { size?: number; color?: string; weight?: number; maxWidth?: number }> = ({
  delay = 0, size = 88, color = C.ink, weight = 800, maxWidth = 1300, style, children,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const words = String(children).split(" ");
  return (
    <div style={{ fontFamily: FONT, fontSize: size, fontWeight: weight, color, letterSpacing: -size * 0.035, lineHeight: 1.04, maxWidth, display: "flex", flexWrap: "wrap", columnGap: size * 0.26, ...style }}>
      {words.map((w, i) => {
        const k = sp(frame, fps, delay + i * 2.2, SPRING);
        return (
          <span key={i} style={{ display: "inline-block", overflow: "hidden", paddingBottom: size * 0.12, marginBottom: -size * 0.12 }}>
            <span style={{ display: "inline-block", transform: `translateY(${(1 - k) * size * 1.05}px)` }}>{w}</span>
          </span>
        );
      })}
    </div>
  );
};

export const Body: React.FC<Base & { size?: number; color?: string; maxWidth?: number; weight?: number }> = ({
  delay = 0, size = 34, color = C.ink, maxWidth = 1100, weight = 500, style, children,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const k = sp(frame, fps, delay);
  return (
    <div style={{ fontFamily: FONT, fontSize: size, fontWeight: weight, color, lineHeight: 1.35, maxWidth, opacity: clamp01(k * 1.5), transform: `translateY(${(1 - k) * 20}px)`, ...style }}>
      {children}
    </div>
  );
};

export const Label: React.FC<Base & { color?: string; bg?: string; size?: number }> = ({
  delay = 0, color = C.surface, bg = C.ink, size = 20, style, children,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const k = sp(frame, fps, delay);
  return (
    <div style={{
      display: "inline-flex", alignItems: "center", fontFamily: FONT, fontSize: size, fontWeight: 700, letterSpacing: size * 0.06, textTransform: "uppercase",
      color, background: bg, padding: `${size * 0.45}px ${size * 0.9}px`, borderRadius: size * 0.5, opacity: clamp01(k * 1.5), transform: `scale(${0.9 + 0.1 * k})`, transformOrigin: "left center", ...style,
    }}>{children}</div>
  );
};

/** Source line: small, muted, inside the gutter (never in a corner). */
export const Source: React.FC<Base> = ({ delay = 0, children, style }) => (
  <Body delay={delay} size={20} color={C.muted} weight={500} style={{ position: "absolute", left: MARGIN, bottom: 118, maxWidth: W - 2 * MARGIN, ...style }}>{children}</Body>
);

/** Burned-in narration line, centred above the bottom gutter. */
export const Subtitle: React.FC<{ chunks: Chunk[]; t: number }> = ({ chunks, t }) => {
  const c = chunks.find((x) => t >= x.from && t < x.to);
  if (!c) return null;
  const age = t - c.from;
  const k = clamp01(age / 0.18);
  return (
    <div style={{ position: "absolute", left: 0, right: 0, bottom: 44, display: "flex", justifyContent: "center", pointerEvents: "none" }}>
      <div style={{
        fontFamily: FONT, fontSize: 30, fontWeight: 500, color: C.surface, background: "rgba(25,40,57,0.86)",
        padding: "12px 22px", borderRadius: 12, maxWidth: 1400, textAlign: "center", lineHeight: 1.3,
        opacity: k, transform: `translateY(${(1 - k) * 8}px)`,
      }}>{c.text}</div>
    </div>
  );
};
