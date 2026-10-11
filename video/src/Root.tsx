import React from "react";
import { AbsoluteFill, Audio, CalculateMetadataFunction, Composition, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { FPS, H, W, fontsReady } from "./brand";
import { chunks, Manifest } from "./lib/vo";
import { Subtitle } from "./ui/Text";
import { BEATS, Clips, sceneSeconds } from "./timeline";
import * as P from "./scenes/problem";
import * as S from "./scenes/stories";
import * as B from "./scenes/box";
import * as A from "./scenes/arch";

type Props = { vo: Manifest; clips: Clips; subtitles: boolean };

const STORIES: Record<string, { title: string; who: string; art: string; steps: string[] }> = {
  story_supervisor: { title: "Ramesh registers his site and his crew", who: "Story 1 · the supervisor", art: "gen/test_sun.png",
    steps: ["/register Ramesh Tower, Kharghar", "Construction site", "40 log, 10 bhaari kaam, 3 naye aaye", "Pehra reads it back: Haan, sahi", "/call_on: Hindi call alerts"] },
  story_supervisor_plan: { title: "Tomorrow's plan, as text and a Hindi voice note", who: "Story 1 · the supervisor", art: "gen/test_sun.png",
    steps: ["plan", "stop work 9–5, rest bands around it", "heavy work stopped, new workers at 20%", "7 water cans", "voice note, then Approve → record"] },
  story_worker: { title: "Gurpreet scans the QR. No app. He taps chakkar.", who: "Story 2 · the worker", art: "gen/kiln.png",
    steps: ["links: QR page + poster", "worker page opens", "Aaram shuru: rest logged", "Chakkar aa raha hai: fixed first aid", "supervisor alerted on WhatsApp, then a Hindi call"] },
  story_ask: { title: "Ask anything. Loosen nothing.", who: "Story 1 · the supervisor", art: "gen/test_sun.png",
    steps: ["Kya hum kal 2 baje concrete daal sakte hain?", "answer from the plan's own tools", "Override → Dheela → a written reason", "saved to the record (Cedar)"] },
  story_family: { title: "Meena's family plan, and a call for Dadi", who: "Story 3 · the family", art: "gen/family_home.png",
    steps: ["hi → Mere aur parivar ke liye", "Mumbai; five button questions", "today: khatarnak, stricter for the vulnerable", "/family_call → Dadi's phone rings", "a Hindi call: stay inside 9 to 5"] },
  story_vendor: { title: "Lakshmi asks: paani, Connaught Place", who: "Story 4 · the vendor", art: "gen/vendor.png",
    steps: ["paani Connaught Place", "nearest drinking water: 190 m", "map link, OpenStreetMap + community points"] },
};

const Scene: React.FC<{ beat: (typeof BEATS)[number]; vo: Manifest; clips: Clips }> = ({ beat, vo, clips }) => {
  const track = vo[beat.vo];
  const p = { track };
  switch (beat.key) {
    case "open": return <P.Open {...p} />;
    case "humidity": return <P.Humidity {...p} />;
    case "wbgt": return <P.Wbgt {...p} />;
    case "kharghar": return <P.Kharghar {...p} />;
    case "kharghar_wbgt": return <P.KharghatChart {...p} />;
    case "audit": return <P.Audit {...p} />;
    case "water": return <P.Water {...p} />;
    case "intro": return <S.Intro {...p} />;
    case "box_why": return <B.BoxWhy {...p} />;
    case "box_what": return <B.BoxWhat {...p} />;
    case "box_does": return <B.BoxDoes {...p} />;
    case "box_sim": return <B.BoxSim {...p} />;
    case "box_twin": return <B.BoxTwin {...p} sos={clips.wa_sos} twin={clips.wa_twin} />;
    case "arch": return <A.Arch {...p} />;
    case "honest": return <A.Honest {...p} />;
    case "outro": return <A.Outro {...p} />;
    default: {
      const s = STORIES[beat.key];
      return <S.Story {...p} {...s} clips={(beat.clips ?? []).map((k) => ({ key: k, meta: clips[k] }))} />;
    }
  }
};

const Video: React.FC<Props> = ({ vo, clips, subtitles }) => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();
  let from = 0;
  const items = BEATS.map((b) => { const f = from; const n = Math.round(sceneSeconds(b, vo, clips) * fps); from += n; return { b, from: f, n }; });
  const t = frame / fps;
  return (
    <AbsoluteFill style={{ background: "#f5f1e8" }}>
      {items.map(({ b, from, n }) => (
        <Sequence key={b.key} from={from} durationInFrames={n} name={b.key}>
          <Scene beat={b} vo={vo} clips={clips} />
          {vo[b.vo] && <Sequence from={Math.round(0.5 * fps)} layout="none"><Audio src={staticFile(vo[b.vo].file)} /></Sequence>}
        </Sequence>
      ))}
      {subtitles && items.map(({ b, from, n }) => {
        if (frame < from || frame >= from + n || !vo[b.vo]) return null;
        return <Subtitle key={b.key} chunks={chunks(vo[b.vo])} t={t - from / fps - 0.5} />;
      })}
    </AbsoluteFill>
  );
};

const calculateMetadata: CalculateMetadataFunction<Props> = async ({ props }) => {
  const [vo, clips] = await Promise.all([
    fetch(staticFile("vo/manifest.json")).then((r) => r.json()) as Promise<Manifest>,
    fetch(staticFile("phone/clips/manifest.json")).then((r) => r.json()) as Promise<Clips>,
  ]);
  await fontsReady;
  const secs = BEATS.reduce((s, b) => s + sceneSeconds(b, vo, clips), 0);
  return { props: { ...props, vo, clips }, durationInFrames: Math.round(secs * FPS) };
};

export const RemotionRoot: React.FC = () => (
  <Composition id="Pehra" component={Video} width={W} height={H} fps={FPS} durationInFrames={300}
    defaultProps={{ vo: {}, clips: {}, subtitles: true }} calculateMetadata={calculateMetadata} />
);
