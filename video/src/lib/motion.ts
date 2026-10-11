// Motion helpers: springs with a tiny overshoot, staggered reveals, and time-based easing. No randomness.
import { interpolate, spring } from "remotion";

export type SpringCfg = { damping: number; stiffness: number; mass: number };
export const SPRING: SpringCfg = { damping: 18, stiffness: 140, mass: 0.9 }; // settles with a 2–3% overshoot
export const SPRING_SOFT: SpringCfg = { damping: 22, stiffness: 90, mass: 1 };
export const SPRING_SNAP: SpringCfg = { damping: 16, stiffness: 220, mass: 0.7 };

export function sp(frame: number, fps: number, delay = 0, config: SpringCfg = SPRING, durationInFrames?: number): number {
  return spring({ frame: frame - delay, fps, config, durationInFrames });
}

export function clamp01(x: number): number {
  return x < 0 ? 0 : x > 1 ? 1 : x;
}

export function ease(frame: number, from: number, to: number, outFrom = 0, outTo = 1): number {
  return interpolate(frame, [from, to], [outFrom, outTo], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
}

/** Cubic ease-out for non-spring movement (camera pans). */
export function easeOut(k: number): number {
  const t = clamp01(k);
  return 1 - (1 - t) ** 3;
}

export function easeInOut(k: number): number {
  const t = clamp01(k);
  return t < 0.5 ? 4 * t ** 3 : 1 - (-2 * t + 2) ** 3 / 2;
}

/** Enter from below with a spring: returns style for translateY + opacity. */
export function rise(frame: number, fps: number, delay = 0, px = 28, config: SpringCfg = SPRING) {
  const k = sp(frame, fps, delay, config);
  return { opacity: clamp01(k * 1.6), transform: `translateY(${(1 - k) * px}px)` };
}

export function scaleIn(frame: number, fps: number, delay = 0, from = 0.92, config: SpringCfg = SPRING) {
  const k = sp(frame, fps, delay, config);
  return { opacity: clamp01(k * 1.6), transform: `scale(${from + (1 - from) * k})` };
}

/** Exit: fades and lifts over `len` frames ending at `end`. */
export function leave(frame: number, end: number, len = 10, px = -18) {
  const k = ease(frame, end - len, end);
  return { opacity: 1 - k, transform: `translateY(${easeOut(k) * px}px)` };
}

/** A count-up that lands exactly on `value`. */
export function countUp(frame: number, fps: number, delay: number, value: number, seconds = 1.4): number {
  const k = ease(frame, delay, delay + seconds * fps);
  return Math.round(value * easeOut(k));
}

export const fmt = (n: number) => n.toLocaleString("en-IN");
