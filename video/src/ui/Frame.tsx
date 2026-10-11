import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT, MARGIN } from "../brand";
import { clamp01, sp } from "../lib/motion";
import { Logo } from "./Logo";

/** The page every scene is drawn on: paper, a small Pehra mark in the top gutter, and an act label. */
export const Frame: React.FC<{ act?: string; dark?: boolean; children: React.ReactNode; bg?: string }> = ({ act, dark = false, bg, children }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const k = sp(frame, fps, 2);
  return (
    <AbsoluteFill style={{ background: bg ?? (dark ? C.navy : C.paper), overflow: "hidden" }}>
      {children}
      <div style={{ position: "absolute", left: MARGIN, top: 54, display: "flex", alignItems: "center", gap: 22 }}>
        <Logo size={34} deva={false} color={dark ? C.surface : C.ink} />
        {act && (
          <div style={{ fontFamily: FONT, fontSize: 18, fontWeight: 600, letterSpacing: 2, textTransform: "uppercase", color: dark ? "rgba(255,253,248,0.7)" : C.muted, opacity: clamp01(k * 1.4), transform: `translateX(${(1 - k) * -10}px)`, paddingLeft: 22, borderLeft: `2px solid ${dark ? "rgba(255,253,248,0.3)" : C.line}` }}>{act}</div>
        )}
      </div>
    </AbsoluteFill>
  );
};

/** Card with the site's surface colour and a hairline, no shadow blur. */
export const Card: React.FC<{ x: number; y: number; w: number; h?: number; delay?: number; dark?: boolean; children?: React.ReactNode; pad?: number; style?: React.CSSProperties }> = ({
  x, y, w, h, delay = 0, dark = false, children, pad = 36, style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const k = sp(frame, fps, delay);
  return (
    <div style={{
      position: "absolute", left: x, top: y, width: w, height: h, padding: pad, boxSizing: "border-box",
      background: dark ? "rgba(255,253,248,0.06)" : C.surface, border: `1.5px solid ${dark ? "rgba(255,253,248,0.16)" : C.line}`, borderRadius: 22,
      opacity: clamp01(k * 1.5), transform: `translateY(${(1 - k) * 24}px)`, fontFamily: FONT, ...style,
    }}>{children}</div>
  );
};
