// Act 3: the Pehra Site Box: why, what each part does, what it acts on, the simulation, the twin.
import React from "react";
import { Audio, OffthreadVideo, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT, LEVELS, MARGIN } from "../brand";
import { clamp01, sp, SPRING_SOFT } from "../lib/motion";
import { at } from "../lib/vo";
import { Card, Frame } from "../ui/Frame";
import { Illustration, Phone } from "../ui/Media";
import { Body, Headline, Label, Source } from "../ui/Text";
import type { ClipMeta, SceneProps } from "../timeline";

const ACT = "The Site Box";

export const BoxWhy: React.FC<SceneProps> = ({ track }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tBox = Math.round(at(track, "box", 3.6) * fps);
  return (
    <Frame act={ACT} dark>
      <div style={{ position: "absolute", left: MARGIN, top: 300, width: 1500 }}>
        <Headline delay={2} size={84} color={C.surface}>Some sites have no smartphone at all.</Headline>
        {frame > tBox && <Headline delay={tBox} size={84} color={C.saffron} style={{ marginTop: 20 }}>For them, Pehra is a box.</Headline>}
      </div>
    </Frame>
  );
};

const PARTS: [string, string, string, number, number][] = [
  ["DHT22", "air temperature + humidity", "the wet-bulb part of WBGT", 0.34, 0.26],
  ["Black globe · DS18B20", "radiant heat from sun, tin and concrete", "the globe part of WBGT", 0.5, 0.12],
  ["2 × HC-SR04 sonar", "drinking-water tank level + drain level", "refill, and waterlogging alerts", 0.62, 0.72],
  ["ESP32", "WiFi, TLS, 10-second readings", "about ₹600 of parts in all", 0.46, 0.45],
];

export const BoxWhat: React.FC<SceneProps> = ({ track }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tA = Math.round(at(track, "humidity", 5.2) * fps);
  const tB = Math.round(at(track, "probe", 7.6) * fps);
  const tC = Math.round(at(track, "sonar", 17.5) * fps);
  const tE = Math.round(at(track, "E", 2.6) * fps);
  const when = [tA, tB, tC, tE];
  return (
    <Frame act={ACT}>
      <Illustration src="gen/sitebox.png" x={MARGIN} y={120} w={880} h={860} radius={24} zoom={1.04} />
      <div style={{ position: "absolute", left: 1080, top: 150, width: 720 }}>
        <Headline delay={2} size={56}>What is inside, and what each part measures</Headline>
        <div style={{ marginTop: 34, display: "flex", flexDirection: "column", gap: 16 }}>
          {PARTS.map(([name, does, why], i) => {
            const k = sp(frame, fps, when[i]);
            return (
              <div key={name} style={{ background: C.surface, border: `1.5px solid ${C.line}`, borderRadius: 18, padding: "18px 24px", opacity: clamp01(k * 1.5), transform: `translateX(${(1 - k) * 36}px)` }}>
                <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                  <div style={{ width: 14, height: 14, borderRadius: 7, background: C.saffron }} />
                  <div style={{ fontFamily: FONT, fontSize: 30, fontWeight: 800, color: C.ink }}>{name}</div>
                </div>
                <div style={{ fontFamily: FONT, fontSize: 24, color: C.ink, marginTop: 6 }}>{does}</div>
                <div style={{ fontFamily: FONT, fontSize: 20, color: C.muted, marginTop: 2 }}>{why}</div>
              </div>
            );
          })}
        </div>
      </div>
      <Source delay={30}>Site WBGT = 0.7·Tnw + 0.2·Tg + 0.1·Ta (Stull wet bulb) · firmware: devices/sitebox · contract: docs/SITEBOX_CONTRACT.md</Source>
    </Frame>
  );
};

const ACTS: [string, string, string][] = [
  ["LED ring", "shows the risk colour", "kam → khatarnak"],
  ["Siren", "rings when it is time to rest", "aaram abhi"],
  ["Relay 1", "turns on a mist fan", "from zyada"],
  ["Relay 2", "refills the water tank", "pump on below 20%"],
  ["Red button", "SOS: WhatsApp alert + Hindi call", "to the supervisor"],
];

export const BoxDoes: React.FC<SceneProps> = ({ track }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t0 = Math.round(at(track, "ring", 3.0) * fps);
  const when = [t0, Math.round(at(track, "siren", 5.0) * fps), Math.round(at(track, "relay", 8.0) * fps), Math.round(at(track, "Another", 10.5) * fps), Math.round(at(track, "red", 12.5) * fps)];
  const kRing = sp(frame, fps, t0, SPRING_SOFT);
  return (
    <Frame act={ACT}>
      <div style={{ position: "absolute", left: MARGIN, top: 160 }}>
        <Headline delay={2} size={64}>It does not just measure. It acts.</Headline>
      </div>
      <div style={{ position: "absolute", left: MARGIN, top: 330, width: 560, height: 560 }}>
        {LEVELS.map((col, i) => {
          const a = (i / LEVELS.length) * Math.PI * 2 - Math.PI / 2;
          const cx = 280 + Math.cos(a) * 200, cy = 280 + Math.sin(a) * 200;
          const k = sp(frame, fps, t0 + i * 3);
          return <div key={i} style={{ position: "absolute", left: cx - 36, top: cy - 36, width: 72, height: 72, borderRadius: 36, background: col, transform: `scale(${k})` }} />;
        })}
        <div style={{ position: "absolute", left: 180, top: 180, width: 200, height: 200, borderRadius: 100, background: C.saffron, transform: `scale(${kRing})`, boxShadow: `inset 0 0 0 10px ${C.ink}` }} />
      </div>
      <div style={{ position: "absolute", left: 820, top: 310, width: 980 }}>
        {ACTS.map(([a, b, c], i) => {
          const k = sp(frame, fps, when[i]);
          return (
            <div key={a} style={{ display: "flex", alignItems: "center", gap: 26, height: 96, opacity: clamp01(k * 1.5), transform: `translateX(${(1 - k) * 40}px)` }}>
              <div style={{ width: 230, fontFamily: FONT, fontSize: 32, fontWeight: 800, color: C.ink }}>{a}</div>
              <div style={{ width: 24, height: 4, background: C.saffron }} />
              <div style={{ fontFamily: FONT, fontSize: 30, color: C.ink, fontWeight: 600 }}>{b}</div>
              <div style={{ fontFamily: FONT, fontSize: 22, color: C.muted }}>{c}</div>
            </div>
          );
        })}
      </div>
    </Frame>
  );
};

const FLOW = ["Site Box", "AWS IoT Core", "IoT rule", "Lambda", "command back"];

export const BoxSim: React.FC<SceneProps> = ({ track }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tCore = Math.round(at(track, "AWS", 6.5) * fps);
  return (
    <Frame act={ACT} dark>
      <div style={{ position: "absolute", left: MARGIN, top: 120, width: 1060, height: 620, borderRadius: 20, overflow: "hidden", border: "1.5px solid rgba(255,253,248,0.2)", opacity: sp(frame, fps, 4) }}>
        <OffthreadVideo src={staticFile("clips/wokwi.mp4")} muted style={{ width: 1060, height: 793, objectFit: "cover", objectPosition: "top" }} />
        <div style={{ position: "absolute", left: 20, bottom: 18 }}><Label delay={10} size={16}>Wokwi ESP32 simulator · real firmware · simulated hardware</Label></div>
      </div>
      <div style={{ position: "absolute", left: 1240, top: 140, width: 560 }}>
        <Headline delay={2} size={46} color={C.surface}>Running, with the real firmware</Headline>
        <Body delay={12} size={24} color="rgba(255,253,248,0.75)" style={{ marginTop: 16 }}>Hot day: WBGT 35.7 °C → KHATARNAK, 60 min rest, KAAM BAND on the OLED; the ring, fan and pump follow the server's command.</Body>
      </div>
      <div style={{ position: "absolute", left: MARGIN, top: 800, right: MARGIN }}>
        <div style={{ display: "flex", alignItems: "center", gap: 0 }}>
          {FLOW.map((s, i) => {
            const k = sp(frame, fps, tCore + i * 9);
            const lead = ((frame - tCore) / fps / 2.4) % 1;
            const here = Math.floor(lead * FLOW.length) === i && frame > tCore + 40;
            return (
              <React.Fragment key={s}>
                <div style={{ fontFamily: FONT, fontSize: 28, fontWeight: 700, color: here ? C.ink : C.surface, background: here ? C.saffron : "rgba(255,253,248,0.08)", border: "1.5px solid rgba(255,253,248,0.2)", borderRadius: 14, padding: "16px 26px", opacity: clamp01(k * 1.5), transform: `translateY(${(1 - k) * 16}px)` }}>{s}</div>
                {i < FLOW.length - 1 && <div style={{ flex: 1, height: 3, background: "rgba(255,253,248,0.25)", transform: `scaleX(${sp(frame, fps, tCore + i * 9 + 5)})`, transformOrigin: "left" }} />}
              </React.Fragment>
            );
          })}
        </div>
        <Body delay={tCore + 40} size={20} color="rgba(255,253,248,0.65)" style={{ marginTop: 18 }}>MQTT over TLS with an X.509 certificate · topic pehra/box/&#123;thing&#125;/telemetry · the policy lets a box publish only to its own topic · HTTPS with a device token as fallback</Body>
      </div>
    </Frame>
  );
};

export const BoxTwin: React.FC<SceneProps & { sos: ClipMeta; twin: ClipMeta; tailAudio?: string }> = ({ track, sos, tailAudio }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tSos = Math.round(at(track, "SOS", 9.0) * fps);
  const twinW = 1180, twinH = Math.round(twinW * 9 / 16);
  return (
    <Frame act={ACT}>
      <div style={{ position: "absolute", left: MARGIN, top: 150, width: twinW, height: twinH, borderRadius: 20, overflow: "hidden", border: `1.5px solid ${C.line}`, opacity: sp(frame, fps, 4) }}>
        <OffthreadVideo src={staticFile("clips/twin.mp4")} muted startFrom={60} style={{ width: twinW, height: twinH, objectFit: "cover" }} />
        <div style={{ position: "absolute", left: 20, bottom: 18 }}><Label delay={10} size={16}>live 3D twin · Three.js · polls the box state every 3 s</Label></div>
      </div>
      <div style={{ position: "absolute", left: 1360, top: 150, width: 440 }}>
        <Headline delay={2} size={46}>Every box gets a live 3D twin</Headline>
        <Body delay={14} size={24} color={C.muted} style={{ marginTop: 14 }}>Risk, rest, tank, drain, fan, pump, SOS: the same state the box shows, on the web.</Body>
      </div>
      {tailAudio ? (
        <>
          <Sequence from={tSos} durationInFrames={Math.max(1, Math.round((0.75 + (track?.dur ?? 10)) * fps) - tSos)} layout="none">
            <Phone src={`phone/clips/wa_sos.mp4`} x={1380} y={430} h={560} delay={0} from={0} muted />
          </Sequence>
          <Sequence from={Math.round((0.75 + (track?.dur ?? 10)) * fps)} layout="none">
            <Phone src={`phone/clips/wa_sos.mp4`} x={1380} y={430} h={560} delay={-30} from={15.5} muted />
            <Audio src={staticFile(tailAudio)} volume={1} />
          </Sequence>
        </>
      ) : (
        <Sequence from={tSos} layout="none">
          <Phone src={`phone/clips/wa_sos.mp4`} x={1380} y={430} h={560} delay={0} from={0} muted />
          <Sequence from={Math.round(sos.calls[0]?.at ?? 18.5) * fps} layout="none">
            <AudioCall file={sos.calls[0]?.audio} />
          </Sequence>
        </Sequence>
      )}
      {frame > tSos && <div style={{ position: "absolute", left: 1380 + 300, top: 440 }}><Label delay={tSos} bg={C.red} size={18}>SOS, on the phone</Label></div>}
      <Source delay={30}>Twin and SOS clip recorded live on 11 Oct 2026 · readings published to IoT Core from a laptop script for the demo</Source>
    </Frame>
  );
};

const AudioCall: React.FC<{ file?: string }> = ({ file }) =>
  file ? <Audio src={staticFile(`phone/clips/${file.split("/").pop()}`)} volume={0.9} /> : null;
