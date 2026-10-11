import React from "react";
import { Img, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { C } from "../brand";
import { clamp01, easeOut, sp } from "../lib/motion";

/** A phone bezel playing one of the real recordings (720x1600 → fits the given height). */
export const Phone: React.FC<{ src: string; x: number; y: number; h: number; delay?: number; from?: number; volume?: number; muted?: boolean; rate?: number }> = ({
  src, x, y, h, delay = 0, from = 0, volume = 1, muted = false, rate = 1,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const k = sp(frame, fps, delay);
  const w = h * 0.47;
  const bez = 14;
  return (
    <div style={{ position: "absolute", left: x, top: y + (1 - k) * 40, opacity: clamp01(k * 1.5) }}>
      <div style={{ width: w + 2 * bez, height: h + 2 * bez, borderRadius: 48, background: C.ink, padding: bez, boxSizing: "border-box" }}>
        <div style={{ width: w, height: h, borderRadius: 36, overflow: "hidden", background: "#000" }}>
          {frame >= delay && (
            <OffthreadVideo src={staticFile(src)} startFrom={Math.round(from * fps)} playbackRate={rate} style={{ width: w, height: h, objectFit: "cover" }} volume={volume} muted={muted} />
          )}
        </div>
      </div>
    </div>
  );
};

/** An illustration (Codex-generated) with a slow push-in; `focus` is the point to drift toward (0–1). */
export const Illustration: React.FC<{ src: string; x?: number; y?: number; w?: number; h?: number; delay?: number; zoom?: number; focus?: [number, number]; radius?: number; dim?: number }> = ({
  src, x = 0, y = 0, w = 1920, h = 1080, delay = 0, zoom = 1.06, focus = [0.5, 0.5], radius = 0, dim = 0,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const k = sp(frame, fps, delay);
  const d = easeOut(frame / Math.max(1, durationInFrames));
  const z = 1 + (zoom - 1) * d;
  return (
    <div style={{ position: "absolute", left: x, top: y, width: w, height: h, overflow: "hidden", borderRadius: radius, opacity: clamp01(k * 1.4) }}>
      <Img src={staticFile(src)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${z})`, transformOrigin: `${focus[0] * 100}% ${focus[1] * 100}%` }} />
      {dim > 0 && <div style={{ position: "absolute", inset: 0, background: `rgba(25,40,57,${dim})` }} />}
    </div>
  );
};

/** A screenshot of the live site, panned to a region, with highlight boxes that draw on. */
export const Site: React.FC<{
  src: string; imgW: number; imgH: number; x: number; y: number; w: number; h: number; delay?: number;
  view: { x: number; y: number; w: number }; // region of the image to show (image px); height follows the aspect
  highlights?: { x: number; y: number; w: number; h: number; at: number; label?: string }[]; // image px, at = seconds
}> = ({ src, imgW, imgH, x, y, w, h, delay = 0, view, highlights = [] }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const k = sp(frame, fps, delay);
  const scale = w / view.w;
  return (
    <div style={{ position: "absolute", left: x, top: y, width: w, height: h, overflow: "hidden", borderRadius: 18, border: `1.5px solid ${C.line}`, background: C.surface, opacity: clamp01(k * 1.5), transform: `translateY(${(1 - k) * 24}px)` }}>
      <div style={{ position: "absolute", left: -view.x * scale, top: -view.y * scale, width: imgW * scale, height: imgH * scale }}>
        <Img src={staticFile(src)} style={{ width: "100%", height: "100%" }} />
        {highlights.map((hl, i) => {
          const kk = sp(frame, fps, Math.round(hl.at * fps));
          return (
            <div key={i} style={{ position: "absolute", left: hl.x * scale - 10, top: hl.y * scale - 8, width: hl.w * scale + 20, height: hl.h * scale + 16, border: `${3 / scale > 3 ? 3 : 3}px solid ${C.saffron}`, borderRadius: 10, boxSizing: "border-box", opacity: clamp01(kk * 1.5), transform: `scale(${0.96 + 0.04 * kk})` }}>
              {hl.label && (
                <div style={{ position: "absolute", left: -3, top: -42, background: C.saffron, color: C.ink, fontWeight: 700, fontSize: 20, padding: "6px 12px", borderRadius: 8, whiteSpace: "nowrap", fontFamily: "Inter" }}>{hl.label}</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
