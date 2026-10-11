// Act 4: the architecture, drawn as a hand-sketched (Excalidraw-style) diagram that draws itself on.
import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT, MARGIN } from "../brand";
import { clamp01, ease, easeOut, sp } from "../lib/motion";
import { at } from "../lib/vo";
import { Frame } from "../ui/Frame";
import { Body, Headline, Label, Source } from "../ui/Text";
import { Logo } from "../ui/Logo";
import type { SceneProps } from "../timeline";

type Node = { id: string; x: number; y: number; w: number; label: string; sub: string; row: number };
const NW = 300, NH = 96;
const COLS = [MARGIN + 40, MARGIN + 470, MARGIN + 900, MARGIN + 1330];
const ROWS = [250, 470, 690, 900];
const N: Node[] = [
  { id: "meteo", x: COLS[0], y: ROWS[0], w: NW, label: "Open-Meteo", sub: "free forecast", row: 0 },
  { id: "sched", x: COLS[1], y: ROWS[0], w: NW, label: "EventBridge", sub: "3× a day", row: 0 },
  { id: "wbgt", x: COLS[2], y: ROWS[0], w: NW, label: "Lambda", sub: "WBGT once per city", row: 0 },
  { id: "s3", x: COLS[3], y: ROWS[0], w: NW, label: "S3", sub: "heat store", row: 0 },
  { id: "wa", x: COLS[0], y: ROWS[1], w: NW, label: "WhatsApp", sub: "Cloud API", row: 1 },
  { id: "api", x: COLS[1], y: ROWS[1], w: NW, label: "API Gateway", sub: "webhooks, pages", row: 1 },
  { id: "bot", x: COLS[2], y: ROWS[1], w: NW, label: "Lambda", sub: "bot + plans", row: 1 },
  { id: "sfn", x: COLS[3], y: ROWS[1], w: NW, label: "Step Functions", sub: "waits for Approve", row: 1 },
  { id: "sqs", x: COLS[0], y: ROWS[2], w: NW, label: "SQS + DLQ", sub: "rate-limited sends", row: 2 },
  { id: "polly", x: COLS[1], y: ROWS[2], w: NW, label: "Polly", sub: "Hindi voice + calls", row: 2 },
  { id: "cedar", x: COLS[2], y: ROWS[2], w: NW, label: "Cedar", sub: "never loosen a plan", row: 2 },
  { id: "bedrock", x: COLS[3], y: ROWS[2], w: NW, label: "Bedrock", sub: "Nova Pro + Strands", row: 2 },
  { id: "iot", x: COLS[0], y: ROWS[3], w: NW, label: "IoT Core", sub: "Site Box, MQTT", row: 3 },
  { id: "boxfn", x: COLS[1], y: ROWS[3], w: NW, label: "Lambda", sub: "box state", row: 3 },
  { id: "ddb", x: COLS[2], y: ROWS[3], w: NW, label: "DynamoDB", sub: "sites, people, boxes", row: 3 },
  { id: "lock", x: COLS[3], y: ROWS[3], w: NW, label: "S3 Object Lock", sub: "hash-chained records", row: 3 },
];
const E: [string, string][] = [["meteo", "sched"], ["sched", "wbgt"], ["wbgt", "s3"], ["wa", "api"], ["api", "bot"], ["bot", "sfn"], ["sfn", "bedrock"], ["bedrock", "cedar"], ["cedar", "polly"], ["polly", "sqs"], ["sqs", "wa"], ["iot", "boxfn"], ["boxfn", "ddb"], ["ddb", "lock"], ["bot", "cedar"]];
const byId = Object.fromEntries(N.map((n) => [n.id, n]));

/** A slightly wobbly path between two nodes, like a hand-drawn connector (deterministic wobble). */
function connector(a: Node, b: Node): string {
  const ax = a.x + a.w / 2, ay = a.y + NH / 2, bx = b.x + b.w / 2, by = b.y + NH / 2;
  let x1 = ax, y1 = ay, x2 = bx, y2 = by;
  if (Math.abs(by - ay) < 10) { x1 = ax < bx ? a.x + a.w : a.x; x2 = ax < bx ? b.x : b.x + b.w; }
  else { y1 = ay < by ? a.y + NH : a.y; y2 = ay < by ? b.y : b.y + NH; }
  const mx = (x1 + x2) / 2 + 6, my = (y1 + y2) / 2 - 5;
  return `M ${x1} ${y1} Q ${mx} ${my} ${x2} ${y2}`;
}

const Box: React.FC<{ n: Node; k: number; hot: boolean }> = ({ n, k, hot }) => {
  const len = 2 * (n.w + NH);
  return (
    <g opacity={clamp01(k * 1.4)}>
      <rect x={n.x + 3} y={n.y + 4} width={n.w} height={NH} rx={14} fill={C.ink} opacity={0.12} />
      <rect x={n.x} y={n.y} width={n.w} height={NH} rx={14} fill={hot ? C.saffron : C.surface} stroke={C.ink} strokeWidth={2.5}
        strokeDasharray={len} strokeDashoffset={len * (1 - easeOut(k))} />
      <text x={n.x + 22} y={n.y + 42} fontFamily={FONT} fontSize={27} fontWeight={800} fill={C.ink}>{n.label}</text>
      <text x={n.x + 22} y={n.y + 74} fontFamily={FONT} fontSize={19} fontWeight={500} fill={C.muted}>{n.sub}</text>
    </g>
  );
};

export const Arch: React.FC<SceneProps> = ({ track }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const rowAt = [Math.round(at(track, "forecast", 4.0) * fps), Math.round(at(track, "Step", 9.0) * fps), Math.round(at(track, "Bedrock", 12.5) * fps), Math.round(at(track, "record", 19.0) * fps)];
  const tDeny = Math.round(at(track, "never", 15.5) * fps);
  const kDeny = sp(frame, fps, tDeny, { damping: 12, stiffness: 260, mass: 0.8 });
  return (
    <Frame>
      <div style={{ position: "absolute", left: MARGIN, top: 110, display: "flex", alignItems: "baseline", gap: 30 }}>
        <Headline delay={2} size={50}>How Pehra runs</Headline>
        <Label delay={10} size={18}>one serverless stack · AWS ap-south-1 (Mumbai) · SAM</Label>
      </div>
      <svg width={1920} height={1080} style={{ position: "absolute", left: 0, top: 0 }}>
        {E.map(([a, b], i) => {
          const na = byId[a], nb = byId[b];
          const t = rowAt[Math.max(na.row, nb.row)] + 10 + (i % 4) * 4;
          const k = ease(frame, t, t + 22);
          const d = connector(na, nb);
          return <path key={i} d={d} fill="none" stroke={C.ink} strokeWidth={2.5} strokeLinecap="round" strokeDasharray={1400} strokeDashoffset={1400 * (1 - easeOut(k))} opacity={0.75} />;
        })}
        {N.map((n, i) => <Box key={n.id} n={n} k={sp(frame, fps, rowAt[n.row] + (i % 4) * 5)} hot={n.id === "cedar" && frame > tDeny} />)}
        {/* one saffron packet rides the people row */}
        {(() => {
          const t0 = rowAt[1] + 30;
          if (frame < t0) return null;
          const path = ["wa", "api", "bot", "sfn"].map((id) => byId[id]);
          const u = (((frame - t0) / fps) / 3.2) % 1;
          const seg = Math.min(2, Math.floor(u * 3)), f = u * 3 - seg;
          const a = path[seg], b = path[seg + 1];
          const x = a.x + a.w + (b.x - a.x - a.w) * f, y = a.y + NH / 2;
          return <circle cx={x} cy={y} r={11} fill={C.saffron} stroke={C.ink} strokeWidth={2} />;
        })()}
      </svg>
      {frame > tDeny && (
        <div style={{ position: "absolute", left: COLS[2] + NW / 2 - 110, top: ROWS[2] - 62, fontFamily: FONT, fontSize: 30, fontWeight: 800, color: C.red, background: C.surface, border: `3px solid ${C.red}`, borderRadius: 10, padding: "4px 16px", transform: `rotate(-3deg) scale(${0.6 + 0.4 * kDeny})`, opacity: clamp01(kDeny * 2) }}>AI: loosen? DENY</div>
      )}
      <div style={{ position: "absolute", left: MARGIN + 40, top: ROWS[0] - 36, fontFamily: FONT, fontSize: 17, fontWeight: 700, letterSpacing: 2, color: C.muted, textTransform: "uppercase", opacity: sp(frame, fps, rowAt[0])}}>forecast → WBGT, once per city</div>
      <div style={{ position: "absolute", left: MARGIN + 40, top: ROWS[1] - 36, fontFamily: FONT, fontSize: 17, fontWeight: 700, letterSpacing: 2, color: C.muted, textTransform: "uppercase", opacity: sp(frame, fps, rowAt[1])}}>people: plan, approve, send</div>
      <div style={{ position: "absolute", left: MARGIN + 40, top: ROWS[2] - 36, fontFamily: FONT, fontSize: 17, fontWeight: 700, letterSpacing: 2, color: C.muted, textTransform: "uppercase", opacity: sp(frame, fps, rowAt[2])}}>AI explains, policy guards, voice</div>
      <div style={{ position: "absolute", left: MARGIN + 40, top: ROWS[3] - 36, fontFamily: FONT, fontSize: 17, fontWeight: 700, letterSpacing: 2, color: C.muted, textTransform: "uppercase", opacity: sp(frame, fps, rowAt[3])}}>devices + records</div>
    </Frame>
  );
};

export const Honest: React.FC<SceneProps> = ({ track }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tNot = Math.round(at(track, "not", 1.0) * fps);
  const tDesigned = Math.round(at(track, "designed", 5.5) * fps);
  return (
    <Frame act="What it does not claim" dark>
      <div style={{ position: "absolute", left: MARGIN, top: 240, width: 1500 }}>
        {frame > tNot && <Headline delay={tNot} size={76} color={C.surface}>Not "saves lives". Not medical advice.</Headline>}
        {frame > tDesigned && <Headline delay={tDesigned} size={76} color={C.saffron} style={{ marginTop: 24 }}>Designed to reduce exposure.</Headline>}
        <Body delay={tDesigned + 30} size={32} color="rgba(255,253,248,0.78)" style={{ marginTop: 50 }}>Every number comes from code. The AI explains; it never calculates, and it can never loosen a limit. Records are hash-chained in S3 Object Lock.</Body>
      </div>
    </Frame>
  );
};

export const Outro: React.FC<SceneProps> = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <Frame>
      <div style={{ position: "absolute", left: 0, right: 0, top: 330, display: "flex", flexDirection: "column", alignItems: "center", gap: 30 }}>
        <Logo size={150} delay={2} />
        <Body delay={24} size={40} color={C.muted} weight={600} style={{ textAlign: "center" }}>A guard for the heat you cannot see.</Body>
        <div style={{ marginTop: 50, display: "flex", gap: 20 }}>
          {["github.com/LSUDOKO/Pehra", "Built on AWS", "Team Mavricks"].map((s, i) => (
            <Label key={s} delay={40 + i * 8} size={20}>{s}</Label>
          ))}
        </div>
      </div>
    </Frame>
  );
};
