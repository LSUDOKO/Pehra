// Scene order and durations. Narration lengths come from vo/manifest.json; phone stories last as long as their clips.
import type { Track } from "./lib/vo";

export type ClipMeta = { path: string; dur: number; audio: boolean; speed: number; calls: { at: number; audio: string }[]; beats: { at: number; text: string }[] };
export type Clips = Record<string, ClipMeta>;
export type SceneProps = { track?: Track };

export type Beat = { key: string; vo: string; min: number; clips?: string[]; hold?: number };

// hold = seconds after the narration (or after the clips) before the next scene
export const BEATS: Beat[] = [
  { key: "open", vo: "open", min: 7, hold: 0.8 },
  { key: "humidity", vo: "humidity", min: 11, hold: 0.8 },
  { key: "wbgt", vo: "wbgt", min: 14, hold: 0.8 },
  { key: "kharghar", vo: "kharghar", min: 16, hold: 1.0 },
  { key: "kharghar_wbgt", vo: "kharghar_wbgt", min: 15, hold: 1.2 },
  { key: "audit", vo: "audit", min: 28, hold: 1.2 },
  { key: "water", vo: "water", min: 9, hold: 1.0 },
  { key: "intro", vo: "intro", min: 12, hold: 1.0 },
  { key: "story_supervisor", vo: "story_supervisor", min: 14, clips: ["wa_register", "wa_crew"], hold: 0.6 },
  { key: "story_supervisor_plan", vo: "story_supervisor_plan", min: 14, clips: ["wa_plan"], hold: 0.6 },
  { key: "story_worker", vo: "story_worker", min: 19, clips: ["wa_links", "wa_worker", "wa_alert"], hold: 0.6 },
  { key: "story_ask", vo: "story_ask", min: 14, clips: ["wa_agent", "wa_override"], hold: 0.6 },
  { key: "story_family", vo: "story_family", min: 18, clips: ["wa_hi", "wa_profile", "wa_today", "wa_family"], hold: 0.6 },
  { key: "story_vendor", vo: "story_vendor", min: 14, clips: ["wa_paani"], hold: 0.8 },
  { key: "box_why", vo: "box_why", min: 5, hold: 0.8 },
  { key: "box_what", vo: "box_what", min: 21, hold: 1.0 },
  { key: "box_does", vo: "box_does", min: 15, hold: 1.0 },
  { key: "box_sim", vo: "box_sim", min: 16, hold: 1.0 },
  { key: "box_twin", vo: "box_twin", min: 15, clips: ["wa_sos"], hold: 0.8 },
  { key: "arch", vo: "arch", min: 22, hold: 1.2 },
  { key: "honest", vo: "honest", min: 11, hold: 1.0 },
  { key: "outro", vo: "outro", min: 8, hold: 2.0 },
];

export function sceneSeconds(b: Beat, vo: Record<string, Track>, clips: Clips): number {
  const voDur = (vo[b.vo]?.dur ?? b.min) + 0.6;
  const clipDur = b.clips ? 1.0 + b.clips.reduce((s, k) => s + (clips[k]?.dur ?? 0), 0) : 0;
  return Math.max(b.min, voDur, clipDur) + (b.hold ?? 0.6);
}

// ---- the 6 to 7 minute cut ----
export type Beat2 = { key: string; vo: string; min: number; clipSecs?: number; extra?: number; hold?: number };
export const BEATS2: Beat2[] = [
  { key: "open", vo: "v2_open", min: 7.5, hold: 0.6 },
  { key: "problemSite", vo: "v2_problem", min: 25, hold: 0.8 },
  { key: "kharghar_wbgt", vo: "kharghar_wbgt", min: 15, hold: 0.8 },
  { key: "auditSite", vo: "v2_audit", min: 22, hold: 0.8 },
  { key: "intro", vo: "v2_intro", min: 11, hold: 0.6 },
  { key: "ramesh", vo: "v2_ramesh", min: 20, extra: 13.6, hold: 0.6 },
  { key: "ask", vo: "v2_ask", min: 16, hold: 1.2 },
  { key: "gurpreet", vo: "v2_gurpreet", min: 20, extra: 13.6, hold: 0.6 },
  { key: "meena", vo: "v2_meena", min: 20, extra: 13.6, hold: 0.6 },
  { key: "lakshmi", vo: "v2_lakshmi", min: 15, hold: 2.0 },
  { key: "box_what", vo: "v2_box", min: 20, hold: 0.8 },
  { key: "box_sim", vo: "v2_sim", min: 14, hold: 0.8 },
  { key: "box_twin", vo: "v2_twin", min: 12, extra: 13.6, hold: 0.6 },
  { key: "arch", vo: "v2_arch", min: 19, hold: 1.0 },
  { key: "proof", vo: "v2_proof", min: 34, hold: 0.6 },
  { key: "outro", vo: "v2_outro", min: 11, hold: 2.0 },
];

export function beat2Seconds(b: Beat2, vo: Record<string, Track>): number {
  const voDur = (vo[b.vo]?.dur ?? b.min) + 0.6 + (b.extra ?? 0);
  return Math.max(b.min, voDur, b.clipSecs ?? 0) + (b.hold ?? 0.6);
}
