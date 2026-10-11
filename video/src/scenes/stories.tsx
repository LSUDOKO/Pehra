// Act 2: Pehra, as four complete stories on a real phone. Clips come from out/video/phone (scrcpy, cut per feature).
import React from "react";
import { Audio, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT, MARGIN } from "../brand";
import { clamp01, sp } from "../lib/motion";
import { at } from "../lib/vo";
import { Dot } from "../ui/Dot";
import { Frame } from "../ui/Frame";
import { Illustration, Phone } from "../ui/Media";
import { Body, Headline, Label, Source } from "../ui/Text";
import type { ClipMeta, SceneProps } from "../timeline";

const ACT = "Pehra on WhatsApp";

export const Intro: React.FC<SceneProps> = ({ track }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tGuard = Math.round(at(track, "guard", 1.0) * fps);
  const tTurns = Math.round(at(track, "turns", 7.2) * fps);
  const steps = ["free forecast", "WBGT", "a plan for the day"];
  return (
    <Frame>
      <div style={{ position: "absolute", left: MARGIN, top: 200 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 34 }}>
          <Headline delay={2} size={170} style={{ letterSpacing: -9 }}>Pehra</Headline>
          <div style={{ fontFamily: "Noto Sans Devanagari", fontSize: 120, fontWeight: 700, color: C.saffron, opacity: sp(frame, fps, 12) }}>पहरा</div>
        </div>
        {frame > tGuard && <Body delay={tGuard} size={44} color={C.muted} weight={600}>guard · a heat and water guard on WhatsApp, in Hindi</Body>}
        {frame > tTurns && (
          <div style={{ display: "flex", alignItems: "center", gap: 26, marginTop: 70 }}>
            {steps.map((s, i) => {
              const k = sp(frame, fps, tTurns + i * 14);
              return (
                <React.Fragment key={s}>
                  <div style={{ fontFamily: FONT, fontSize: 40, fontWeight: 700, color: C.ink, background: C.surface, border: `1.5px solid ${C.line}`, borderRadius: 16, padding: "18px 30px", opacity: clamp01(k * 1.5), transform: `translateY(${(1 - k) * 20}px)` }}>{s}</div>
                  {i < steps.length - 1 && <div style={{ width: 60 * sp(frame, fps, tTurns + i * 14 + 8), height: 4, background: C.saffron, borderRadius: 2 }} />}
                </React.Fragment>
              );
            })}
          </div>
        )}
      </div>
      <Dot x={1700} y={300} r={56} delay={4} ring />
      <Source delay={40}>WhatsApp Cloud API (test number for the demo), also on Telegram · forecast: Open-Meteo</Source>
    </Frame>
  );
};

/** A story scene: illustration + headline first, then the real phone clips with the narration's beats as a step list. */
export const Story: React.FC<SceneProps & {
  title: string; who: string; art: string; clips: { key: string; meta: ClipMeta }[]; steps: string[]; stepAt?: number[];
}> = ({ track, title, who, art, clips, steps, stepAt }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tPhone = 30;
  const phoneH = 860;
  // clips play back to back inside the phone
  let start = tPhone;
  const seq = clips.map((c) => { const s = start; start += Math.round(c.meta.dur * fps); return { ...c, start: s }; });
  return (
    <Frame act={ACT}>
      <Illustration src={art} x={0} y={0} w={1920} h={1080} zoom={1.05} dim={0.55} />
      <Phone src={`phone/clips/${clips[0].key}.mp4`} x={MARGIN} y={110} h={phoneH} delay={tPhone} muted={!clips[0].meta.audio} />
      {seq.slice(1).map((c) => (
        <Sequence key={c.key} from={c.start} layout="none">
          <Phone src={`phone/clips/${c.key}.mp4`} x={MARGIN} y={110} h={phoneH} delay={0} muted={!c.meta.audio} />
        </Sequence>
      ))}
      {seq.flatMap((c) => c.meta.calls.map((call, i) => (
        <Sequence key={c.key + i} from={c.start + Math.round(call.at * fps)} layout="none">
          <Audio src={staticFile(`phone/clips/${call.audio.split("/").pop()}`)} volume={0.9} />
        </Sequence>
      )))}
      <div style={{ position: "absolute", left: 680, top: 150, width: 1120 }}>
        <Label delay={2} bg={C.saffron} color={C.ink}>{who}</Label>
        <div style={{ height: 18 }} />
        <Headline delay={6} size={66} color={C.surface}>{title}</Headline>
        <div style={{ marginTop: 44, display: "flex", flexDirection: "column", gap: 16 }}>
          {steps.map((s, i) => {
            const d = stepAt ? Math.round(stepAt[i] * fps) : tPhone + 20 + i * 26;
            const k = sp(frame, fps, d);
            const current = frame >= d && (i === steps.length - 1 || frame < (stepAt ? Math.round(stepAt[i + 1] * fps) : d + 26));
            return (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 18, opacity: clamp01(k * 1.5) * (current ? 1 : 0.55), transform: `translateX(${(1 - k) * 30}px)` }}>
                <div style={{ width: 16, height: 16, borderRadius: 8, background: current ? C.saffron : C.surface, boxShadow: current ? `0 0 0 3px ${C.surface}` : undefined }} />
                <div style={{ fontFamily: FONT, fontSize: current ? 34 : 28, fontWeight: current ? 700 : 500, color: C.surface, lineHeight: 1.25 }}>{s}</div>
              </div>
            );
          })}
        </div>
        <div style={{ marginTop: 40, fontFamily: FONT, fontSize: 20, color: "rgba(255,253,248,0.65)", opacity: sp(frame, fps, tPhone + 10) }}>Real phone recording · moto g34, 11 Oct 2026 · waits shown faster · WhatsApp test number · Twilio trial call</div>
      </div>
    </Frame>
  );
};
