import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT, FONT_DEVA } from "../brand";
import { sp, SPRING_SOFT } from "../lib/motion";

/** The Pehra mark: a saffron dot (the sun, the guard's lamp), the wordmark, and the Devanagari name. */
export const Logo: React.FC<{ size?: number; delay?: number; deva?: boolean; color?: string }> = ({
  size = 64, delay = 0, deva = true, color = C.ink,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const kDot = sp(frame, fps, delay, SPRING_SOFT);
  const kWord = sp(frame, fps, delay + 6);
  const kDeva = sp(frame, fps, delay + 14);
  const dot = size * 0.62;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: size * 0.28, fontFamily: FONT, lineHeight: 1 }}>
      <div style={{
        width: dot, height: dot, borderRadius: dot, background: C.saffron,
        transform: `scale(${kDot})`, boxShadow: `inset 0 0 0 ${size * 0.06}px ${C.ink}`,
      }} />
      <div style={{ overflow: "hidden" }}>
        <div style={{
          fontSize: size, fontWeight: 800, letterSpacing: -size * 0.04, color,
          transform: `translateY(${(1 - kWord) * size}px)`,
        }}>Pehra</div>
      </div>
      {deva && (
        <div style={{ fontFamily: FONT_DEVA, fontSize: size * 0.78, fontWeight: 700, color: C.saffron, opacity: kDeva, transform: `translateX(${(1 - kDeva) * -12}px)` }}>पहरा</div>
      )}
    </div>
  );
};
