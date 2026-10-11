import React from "react";
import { Img, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT } from "../brand";
import { clamp01, easeInOut, sp } from "../lib/motion";

export type View = { at: number; x: number; y: number; w: number }; // image px; at = seconds
export type Mark = { at: number; x: number; y: number; w: number; h: number; label?: string; until?: number };

/**
 * A real screenshot in a browser-like frame. The camera moves between views (eased), and saffron
 * highlight boxes draw on at their cue, so the viewer reads the actual number on the actual page.
 */
export const ZoomShot: React.FC<{
  src: string; imgW: number; imgH: number; x: number; y: number; w: number; h: number;
  views: View[]; marks?: Mark[]; url?: string; delay?: number; move?: number;
}> = ({ src, imgW, imgH, x, y, w, h, views, marks = [], url, delay = 0, move = 0.9 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const k0 = sp(frame, fps, delay);
  const bar = url ? 52 : 0;
  const vh = h - bar;
  // current view: ease from the previous view to the next one over `move` seconds
  let v = views[0];
  for (let i = 1; i < views.length; i++) {
    const a = views[i - 1], b = views[i];
    if (t >= b.at) { v = b; continue; }
    if (t > b.at - move) {
      const e = easeInOut((t - (b.at - move)) / move);
      v = { at: 0, x: a.x + (b.x - a.x) * e, y: a.y + (b.y - a.y) * e, w: a.w + (b.w - a.w) * e };
    }
    break;
  }
  const scale = w / v.w;
  return (
    <div style={{ position: "absolute", left: x, top: y, width: w, height: h, borderRadius: 18, overflow: "hidden", background: C.surface, border: `1.5px solid ${C.line}`, boxShadow: "0 30px 60px -30px rgba(25,40,57,0.35)", opacity: clamp01(k0 * 1.5), transform: `translateY(${(1 - k0) * 30}px)` }}>
      {url && (
        <div style={{ height: bar, display: "flex", alignItems: "center", gap: 10, padding: "0 20px", background: "#ece7db", borderBottom: `1px solid ${C.line}` }}>
          {["#e8695f", "#e8b84b", "#5fbf6a"].map((c) => <div key={c} style={{ width: 13, height: 13, borderRadius: 7, background: c }} />)}
          <div style={{ marginLeft: 14, flex: 1, height: 32, borderRadius: 8, background: C.surface, display: "flex", alignItems: "center", padding: "0 14px", fontFamily: FONT, fontSize: 19, color: C.muted }}>{url}</div>
        </div>
      )}
      <div style={{ position: "relative", width: w, height: vh, overflow: "hidden" }}>
        <div style={{ position: "absolute", left: -v.x * scale, top: -v.y * scale, width: imgW * scale, height: imgH * scale }}>
          <Img src={staticFile(src)} style={{ width: "100%", height: "100%" }} />
          {marks.map((m, i) => {
            if (m.until !== undefined && t > m.until) return null;
            const kk = sp(frame, fps, Math.round(m.at * fps));
            if (kk <= 0.001) return null;
            return (
              <div key={i} style={{ position: "absolute", left: m.x * scale - 8, top: m.y * scale - 8, width: m.w * scale + 16, height: m.h * scale + 16, border: `4px solid ${C.saffron}`, borderRadius: 12, boxSizing: "border-box", background: "rgba(216,139,40,0.10)", opacity: clamp01(kk * 1.5), transform: `scale(${0.94 + 0.06 * kk})` }}>
                {m.label && <div style={{ position: "absolute", left: -4, top: -50, background: C.saffron, color: C.ink, fontWeight: 800, fontSize: 24, padding: "6px 14px", borderRadius: 8, whiteSpace: "nowrap", fontFamily: FONT }}>{m.label}</div>}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
