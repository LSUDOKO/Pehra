import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { C } from "../brand";
import { sp, SPRING_SOFT } from "../lib/motion";

/**
 * The saffron dot is the one element that connects every scene: the sun in the problem, the risk light on the
 * Site Box, the lamp of the guard in the logo. Scenes place it; it springs between positions.
 */
export const Dot: React.FC<{ x: number; y: number; r?: number; delay?: number; ring?: boolean }> = ({ x, y, r = 28, delay = 0, ring = false }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const k = sp(frame, fps, delay, SPRING_SOFT);
  return (
    <div style={{ position: "absolute", left: x - r, top: y - r, width: 2 * r, height: 2 * r, borderRadius: r, background: C.saffron, transform: `scale(${k})`, boxShadow: ring ? `0 0 0 ${Math.max(2, r * 0.12)}px ${C.ink}` : undefined }} />
  );
};
