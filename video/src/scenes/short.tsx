// The 6 to 7 minute cut: real website screenshots with zoom highlights, characters that read the real WhatsApp chats,
// the Site Box, the architecture and the AWS proof screenshots.
import React from "react";
import { Audio, Img, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT, MARGIN } from "../brand";
import { clamp01, ease, sp, SPRING_SOFT } from "../lib/motion";
import { at } from "../lib/vo";
import { Frame } from "../ui/Frame";
import { Phone } from "../ui/Media";
import { Body, Headline, Label } from "../ui/Text";
import { ZoomShot } from "../ui/Zoom";
import { Logo } from "../ui/Logo";
import type { SceneProps } from "../timeline";

const fr = (s: number, fps: number) => Math.round(s * fps);

// ---------------- the problem on the real website ----------------
export const ProblemSite: React.FC<SceneProps> = ({ track }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tK = at(track, "Kharghar", 6.5), tNo = at(track, "alert", 11.5), tW = at(track, "reached", 15), tL = at(track, "limit", 18);
  return (
    <Frame act="The problem">
      <div style={{ position: "absolute", left: MARGIN, top: 130, width: 1680 }}>
        <Headline delay={4} size={52}>Heat and humidity together: WBGT. Not the thermometer.</Headline>
      </div>
      <ZoomShot src="site/site-problem.png" imgW={1440} imgH={615} x={MARGIN} y={240} w={1680} h={740}
        url="yj61i9i7g0.execute-api.ap-south-1.amazonaws.com/#problem" delay={6}
        views={[{ at: 0, x: 60, y: 60, w: 1320 }, { at: tK, x: 760, y: 150, w: 660 }, { at: tL + 2.5, x: 60, y: 60, w: 1320 }]}
        marks={[{ at: tK + 0.4, x: 970, y: 256, w: 350, h: 190, label: "Kharghar, 16 Apr 2023", until: tNo - 0.1 },
          { at: tNo, x: 970, y: 256, w: 350, h: 70, label: "38.8 °C: no heatwave alert", until: tW - 0.2 },
          { at: tW, x: 970, y: 330, w: 350, h: 116, label: "WBGT 30.8 °C vs 28.2 °C limit" }]} />
      {frame > fr(tL, fps) && (
        <div style={{ position: "absolute", right: MARGIN + 30, top: 860, display: "flex", gap: 16 }}>
          <Label delay={fr(tL, fps)} bg={C.red} size={26}>Real. Invisible.</Label>
        </div>
      )}
    </Frame>
  );
};

export const AuditSite: React.FC<SceneProps> = ({ track }) => {
  const t1 = at(track, "4,372", 4.0), t2 = at(track, "2,327", 9.5), t3 = at(track, "caveats", 13.5);
  return (
    <Frame act="The problem">
      <ZoomShot src="site/audit.png" imgW={1440} imgH={2015} x={MARGIN} y={130} w={1680} h={850}
        url="yj61i9i7g0.execute-api.ap-south-1.amazonaws.com/audit" delay={2}
        views={[{ at: 0, x: 180, y: 120, w: 1080 }, { at: t1, x: 200, y: 280, w: 820 }, { at: t2, x: 200, y: 420, w: 820 },
          { at: t3, x: 180, y: 660, w: 1080 }, { at: t3 + 3.2, x: 180, y: 980, w: 1080 }]}
        marks={[{ at: t1 + 0.3, x: 230, y: 313, w: 500, h: 126, label: "4,372 city-days, no alert" },
          { at: t2 + 0.2, x: 230, y: 455, w: 832, h: 79, label: "2,327 outside March to June" },
          { at: t3 + 0.3, x: 230, y: 703, w: 980, h: 204, label: "every caveat, on the page" },
          { at: t3 + 3.6, x: 231, y: 1063, w: 979, h: 140, label: "by city" }]} />
    </Frame>
  );
};

// ---------------- a character reads their WhatsApp chat ----------------
export type Seg = { key: string; from: number; to: number; word?: string; n?: number };
export type Msg = { word: string; n?: number; who: "me" | "bot" | "call"; title?: string; lines: string[] };
export type Tail = { key: string; from: number; callFrom?: number; audio: string; secs: number; title: string; lines: string[]; call: boolean };

const Bubble: React.FC<{ m: Msg; k: number; old: boolean }> = ({ m, k, old }) => {
  const me = m.who === "me";
  const call = m.who === "call";
  return (
    <div style={{
      alignSelf: me ? "flex-end" : "flex-start", maxWidth: 720, background: me ? "#d9fdd3" : call ? C.ink : C.surface,
      border: `1.5px solid ${me ? "#b8e6b0" : call ? C.ink : C.line}`, borderRadius: 22, padding: "20px 26px",
      boxShadow: "0 18px 36px -24px rgba(25,40,57,0.5)", fontFamily: FONT, opacity: clamp01(k * 1.6) * (old ? 0.6 : 1),
      transform: `translateY(${(1 - k) * 26}px) scale(${old ? 0.97 : 1})`, transformOrigin: me ? "right top" : "left top",
    }}>
      {m.title && <div style={{ fontSize: 30, fontWeight: 800, color: call ? C.saffron : C.ink, marginBottom: 8 }}>{m.title}</div>}
      {m.lines.map((l, i) => <div key={i} style={{ fontSize: 30, lineHeight: 1.32, fontWeight: me ? 600 : 500, color: call ? C.surface : C.ink }}>{l}</div>)}
      {!me && !call && <div style={{ fontSize: 18, color: C.muted, marginTop: 8, fontWeight: 600 }}>Pehra · WhatsApp</div>}
    </div>
  );
};

/** A sound-wave meter that moves only while the voice note or call is actually playing. */
const Wave: React.FC<{ t: number; on: boolean }> = ({ t, on }) => (
  <div style={{ display: "flex", gap: 6, alignItems: "center", height: 44, marginTop: 12 }}>
    {Array.from({ length: 22 }).map((_, i) => {
      const h = on ? 10 + 30 * Math.abs(Math.sin(t * 9 + i * 1.3) * Math.sin(t * 3.1 + i)) : 6;
      return <div key={i} style={{ width: 7, height: h, borderRadius: 4, background: C.saffron }} />;
    })}
  </div>
);

export const CharStory: React.FC<SceneProps & { name: string; role: string; poses: [string, string]; segs: Seg[]; msgs: Msg[]; tail?: Tail }> = ({
  track, name, role, poses, segs, msgs, tail,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const t = frame / fps;
  const kIn = sp(frame, fps, 0, SPRING_SOFT);
  const bob = Math.sin(t * 2.2) * 6;
  const voEnd = 0.4 + (track?.dur ?? 10) + 0.35;          // narration plays from 0.4 s
  const tailStart = tail ? voEnd : durationInFrames / fps;
  // each phone clip starts on its narration cue and is stretched to fill the time until the next cue
  const starts = segs.map((s, i) => (i === 0 ? 0 : at(track, s.word ?? "", 3 + i * 4, s.n ?? 0)));
  const plan = segs.map((s, i) => {
    const st = starts[i], en = i + 1 < segs.length ? starts[i + 1] : tailStart;
    const len = Math.max(0.5, en - st);
    return { ...s, st, len, rate: Math.min(4, Math.max(0.5, (s.to - s.from) / len)) };
  });
  const timed = msgs.map((m) => ({ ...m, t: at(track, m.word, 2, m.n ?? 0) + 0.3 }));
  const shown = timed.filter((m) => t >= m.t);
  const tailOn = tail && t >= tailStart;
  const lastTap = shown.length ? shown[shown.length - 1].t : -9;
  const tap = Math.max(0, 1 - (t - lastTap) * 3) * Math.sin(Math.min(1, (t - lastTap) * 3) * Math.PI);
  const swap = tail ? tailStart : durationInFrames / fps * 0.5;
  const ringEnd = tail && tail.call ? tailStart + 2.6 : tailStart;
  return (
    <Frame act="Pehra on WhatsApp">
      <div style={{ position: "absolute", left: MARGIN, top: 118, display: "flex", alignItems: "baseline", gap: 22 }}>
        <Label delay={2} bg={C.saffron} color={C.ink} size={28}>{name}</Label>
        <Body delay={6} size={30} color={C.muted} weight={600}>{role}</Body>
      </div>
      <div style={{ position: "absolute", left: 40, bottom: 0, width: 560, height: 820, display: "flex", alignItems: "flex-end", justifyContent: "center" }}>
        <Img src={staticFile(`chars/${t < swap ? poses[0] : poses[1]}.png`)} style={{
          maxWidth: 540, maxHeight: 800, objectFit: "contain",
          transform: `translateX(${(1 - kIn) * -260}px) translateY(${bob - tap * 14}px) scale(${1 + tap * 0.02})`, opacity: clamp01(kIn * 1.4),
        }} />
      </div>
      {plan.map((s, i) => (
        <Sequence key={s.key + i} from={fr(s.st, fps)} durationInFrames={Math.max(1, fr(s.len, fps))} layout="none">
          <Phone src={`phone/clips/${s.key}.mp4`} x={610} y={190} h={840} delay={i === 0 ? 0 : -30} from={s.from} rate={s.rate} muted />
        </Sequence>
      ))}
      {tail && (
        <Sequence from={fr(tailStart, fps)} layout="none">
          <Audio src={staticFile(tail.audio)} volume={1} />
          <Sequence durationInFrames={tail.callFrom !== undefined ? fr(2.6, fps) : undefined} layout="none">
            <Phone src={`phone/clips/${tail.key}.mp4`} x={610} y={190} h={840} delay={-30} from={tail.from} rate={1} muted />
          </Sequence>
          {tail.callFrom !== undefined && (
            <Sequence from={fr(2.6, fps)} layout="none">
              <Phone src={`phone/clips/${tail.key}.mp4`} x={610} y={190} h={840} delay={-30} from={tail.callFrom} rate={1} muted />
            </Sequence>
          )}
        </Sequence>
      )}
      <div style={{ position: "absolute", left: 610, top: 1040, width: 430, textAlign: "center", fontFamily: FONT, fontSize: 18, color: C.muted, fontWeight: 600 }}>real phone recording</div>
      <div style={{ position: "absolute", left: 1090, top: 200, width: 740, height: 800, display: "flex", flexDirection: "column", gap: 20 }}>
        {!tailOn && shown.slice(-3).map((m, i, arr) => (
          <Bubble key={m.word + m.lines[0]} m={m} k={sp(frame, fps, fr(m.t, fps))} old={i < arr.length - 1 && m.who !== "me"} />
        ))}
        {tailOn && tail && (
          <div style={{ background: tail.call ? C.ink : C.surface, border: `1.5px solid ${tail.call ? C.ink : C.line}`, borderRadius: 22, padding: "24px 28px", fontFamily: FONT, ...{ opacity: clamp01(sp(frame, fps, fr(tailStart, fps)) * 1.6) } }}>
            <div style={{ fontSize: 22, fontWeight: 800, letterSpacing: 1.5, textTransform: "uppercase", color: C.saffron }}>
              {tail.call ? (t < ringEnd ? "Incoming call · ringing" : "On the call · real audio") : "Voice note · real audio"}
            </div>
            <div style={{ fontSize: 32, fontWeight: 800, color: tail.call ? C.surface : C.ink, marginTop: 8 }}>{tail.title}</div>
            <Wave t={t} on={t >= ringEnd} />
            {tail.lines.map((l, i) => <div key={i} style={{ fontSize: 30, lineHeight: 1.34, fontWeight: 500, marginTop: i ? 0 : 12, color: tail.call ? C.surface : C.ink, opacity: t >= ringEnd ? 1 : 0.35 }}>{l}</div>)}
          </div>
        )}
      </div>
    </Frame>
  );
};

// ---------------- AWS proof, from the account ----------------
const PROOF: [string, number, number, string][] = [
  ["proof/stack.png", 4772, 2567, "CloudFormation: the deployed stack"],
  ["proof/iot.png", 3689, 1817, "AWS IoT Core: the Site Box thing, rule and endpoint"],
  ["proof/sfn.png", 3256, 1007, "Step Functions: plan executions"],
  ["proof/lock.png", 2265, 1382, "S3 Object Lock on the records bucket"],
  ["proof/lambda.png", 3720, 1568, "Lambda arm64 with Bedrock · DynamoDB"],
  ["proof/calls.png", 3070, 758, "Twilio: six Hindi calls on 11 October"],
];

export const Proof: React.FC<SceneProps> = () => {
  const { fps, durationInFrames } = useVideoConfig();
  const each = Math.floor(durationInFrames / PROOF.length);
  return (
    <Frame act="Proof from the AWS account">
      {PROOF.map(([src, w, h, label], i) => {
        const boxW = 1680, boxH = 760;
        const s = Math.min(boxW / w, boxH / h);
        const vw = Math.min(w, boxW / s);
        return (
          <Sequence key={src} from={i * each} durationInFrames={each} layout="none">
            <div style={{ position: "absolute", left: MARGIN, top: 130 }}><Label delay={0} size={28}>{label}</Label></div>
            <ZoomShot src={src} imgW={w} imgH={h} x={MARGIN} y={220} w={boxW} h={boxH} delay={0} move={2.6}
              views={[{ at: 0, x: 0, y: 0, w: Math.max(vw, w * 0.98) }, { at: each / fps - 0.2, x: w * 0.02, y: 0, w: Math.max(vw * 0.86, w * 0.84) }]} />
          </Sequence>
        );
      })}
      <div style={{ position: "absolute", left: MARGIN, top: 1000, fontFamily: FONT, fontSize: 22, color: C.muted }}>CLI output rendered with freeze · account id masked</div>
    </Frame>
  );
};

export const OutroShort: React.FC<SceneProps> = ({ track }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tP = fr(at(track, "Pehra", 4.5, 1), fps);
  return (
    <Frame>
      {frame < tP ? (
        <div style={{ position: "absolute", left: MARGIN, top: 300, width: 1500 }}>
          <Headline delay={2} size={72}>Not "saves lives". Not medical advice.</Headline>
          <Headline delay={30} size={72} color={C.saffron} style={{ marginTop: 20 }}>Designed to reduce exposure.</Headline>
        </div>
      ) : (
        <Sequence from={tP} layout="none">
          <div style={{ position: "absolute", left: 0, right: 0, top: 330, display: "flex", flexDirection: "column", alignItems: "center", gap: 30 }}>
            <Logo size={150} delay={0} />
            <Body delay={14} size={42} color={C.muted} weight={600}>A guard for the heat you cannot see.</Body>
            <div style={{ marginTop: 40, display: "flex", gap: 18 }}>
              {["github.com/LSUDOKO/Pehra", "Built on AWS", "Team Mavricks"].map((s, i) => <Label key={s} delay={28 + i * 6} size={24}>{s}</Label>)}
            </div>
          </div>
        </Sequence>
      )}
    </Frame>
  );
};
