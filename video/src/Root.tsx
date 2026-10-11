import React from "react";
import { AbsoluteFill, Audio, CalculateMetadataFunction, Composition, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { FPS, H, W, fontsReady } from "./brand";
import { chunks, Manifest } from "./lib/vo";
import { Subtitle } from "./ui/Text";
import { BEATS, BEATS2, Clips, beat2Seconds, sceneSeconds } from "./timeline";
import * as Sh from "./scenes/short";
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
  <>
    <Composition id="Pehra" component={Video} width={W} height={H} fps={FPS} durationInFrames={300}
      defaultProps={{ vo: {}, clips: {}, subtitles: true }} calculateMetadata={calculateMetadata} />
    <ShortRoot />
  </>
);

// ---------------- the 6 to 7 minute cut ----------------
const M = (word: string, who: Sh.Msg["who"], lines: string[], title?: string, n = 0): Sh.Msg => ({ word, who, lines, title, n });

const Short2: React.FC<{ b: (typeof BEATS2)[number]; vo: Manifest; clips: Clips }> = ({ b, vo, clips }) => {
  const p = { track: vo[b.vo] };
  switch (b.key) {
    case "open": return <P.Open {...p} />;
    case "problemSite": return <Sh.ProblemSite {...p} />;
    case "kharghar_wbgt": return <P.KharghatChart {...p} />;
    case "auditSite": return <Sh.AuditSite {...p} />;
    case "intro": return <S.Intro {...p} />;
    case "ramesh": return <Sh.CharStory {...p} name="Ramesh" role="site supervisor, Kharghar" poses={["ramesh_2", "ramesh_1"]}
      segs={[{ key: "wa_crew", from: 0, to: 15 }, { key: "wa_plan", from: 6, to: 25, word: "tomorrow's" }]}
      msgs={[M("types", "me", ["40 log, 10 bhaari kaam, 3 naye aaye"]),
        M("reads", "bot", ["40 log, 10 bhaari kaam, 3 naye. Sahi hai?", "Haan, sahi  ·  Crew save ho gaya."]),
        M("tomorrow's", "bot", ["Kaam band: subah 9 se shaam 5 baje", "8 se 9 baje: har ghante 15 min aaram", "5 se 6 baje: har ghante 30 min aaram", "Naye mazdoor (3): sirf 20% kaam", "Paani: 7 bade can (20 litre)"], "Kal ka plan (Ramesh Tower)")]}
      tail={{ key: "wa_plan", from: 26, audio: "audio/tail_voice.mp3", secs: 13, call: false, title: "Kal ka plan, in Hindi",
        lines: ["Kal 9 se 5 baje tak kaam rokna hai.", "8 se 9 baje tak har ghante 15 minute aaram.", "5 se 6 baje tak har ghante 30 minute aaram.", "7 bade paani ke can mangwa lo."] }} />;
    case "ask": return <Sh.CharStory {...p} name="Ramesh" role="approves, then asks" poses={["ramesh_3", "ramesh_3"]}
      segs={[{ key: "wa_plan", from: 46, to: 54 }, { key: "wa_agent", from: 0, to: 22, word: "asks" }]}
      msgs={[M("Approve", "me", ["Approve"]),
        M("saved", "bot", ["Plan approve ho gaya. Record mein save hai."]),
        M("asks", "me", ["Kya hum kal dopahar 2 baje concrete daal sakte hain?"]),
        M("answers", "bot", ["Dopahar ka kaam nahi kar sakte.", "Bhaari kaam ke liye rok lagaya gaya hai.", "Plan Open-Meteo forecast par based hai."])]} />;
    case "gurpreet": return <Sh.CharStory {...p} name="Gurpreet" role="worker on Ramesh's site" poses={["gurpreet_1", "ramesh_1"]}
      segs={[{ key: "wa_worker", from: 0, to: 15 }, { key: "wa_worker", from: 26, to: 33, word: "taps" }, { key: "wa_alert", from: 0, to: 11, word: "alert" }]}
      msgs={[M("scans", "bot", ["Ramesh Tower", "[ Aaram shuru ]   [ Chakkar aa raha hai ]"], "Worker page (QR)"),
        M("logs", "me", ["Aaram shuru"]),
        M("taps", "me", ["Chakkar aa raha hai"]),
        M("first", "bot", ["Turant kaam rokiye.", "Chhaon mein jaiye.", "Paani piyiye, dheere dheere."], "First aid"),
        M("alert", "bot", ["Dhyan dein: 14:50 par ek mazdoor ne", "'chakkar aa raha hai' dabaya.", "Turant unke paas jaiye. Uljhan ho to 108."], "To Ramesh")]}
      tail={{ key: "wa_call", from: 15.5, callFrom: 24, audio: "audio/tail_call_symptom.mp3", secs: 13.1, call: true, title: "Pehra calls Ramesh, in Hindi",
        lines: ["Dhyan dein. Aapki site par ek mazdoor ne", "chakkar aane ki khabar di hai.", "Turant unke paas jaiye..."] }} />;
    case "meena": return <Sh.CharStory {...p} name="Meena" role="expecting, with Chotu and Dadi, Mumbai" poses={["meena_and_chotu_1", "dadi_2"]}
      segs={[{ key: "wa_hi", from: 14, to: 24 }, { key: "wa_profile", from: 0, to: 28, word: "questions" }, { key: "wa_today", from: 1, to: 19, word: "reads" }]}
      msgs={[M("says", "me", ["hi  ·  Mere aur parivar ke liye"]),
        M("questions", "me", ["Mumbai  ·  buzurg 1  ·  bachche 1", "garbhvati: Haan  ·  bahar kaam: Haan"]),
        M("reads", "bot", ["Aaj Mumbai: khatarnak", "Buzurg, bachche, garbhvati:", "bahar na jaiye 9 se 5 baje", "Behtar samay: 6 se 9 baje", "Bimar mehsoos ho to 108"], "Aaj ka garmi-plan")]}
      tail={{ key: "wa_family", from: 39.5, callFrom: 44, audio: "audio/tail_call_family.mp3", secs: 13.1, call: true, title: "Pehra calls Dadi, in Hindi",
        lines: ["Aaj Mumbai mein bahut garmi aur nami hai.", "9 se 5 baje tak ghar ke andar rahiye.", "Thoda thoda paani peete rahiye..."] }} />;
    case "lakshmi": return <Sh.CharStory {...p} name="Lakshmi" role="fruit vendor, Delhi" poses={["lakshmi_2", "lakshmi_3"]}
      segs={[{ key: "wa_paani", from: 0, to: 6 }, { key: "wa_paani", from: 6, to: 25, word: "replies" }]}
      msgs={[M("types", "me", ["paani Connaught Place"]),
        M("replies", "bot", ["Peene ka paani: 190 m", "Pi-Lo Smart Water ATM: 220 m", "Peene ka paani: 250 m", "map links · OpenStreetMap"], "Connaught Place · sabse paas")]} />;
    case "box_what": return <B.BoxWhat {...p} />;
    case "box_sim": return <B.BoxSim {...p} />;
    case "box_twin": return <B.BoxTwin {...p} sos={clips.wa_sos} twin={clips.wa_twin} tailAudio="audio/tail_call_sos.mp3" />;
    case "arch": return <A.Arch {...p} />;
    case "proof": return <Sh.Proof {...p} />;
    default: return <Sh.OutroShort {...p} />;
  }
};

const VideoShort: React.FC<Props> = ({ vo, clips, subtitles }) => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();
  let from = 0;
  const items = BEATS2.map((b) => { const f = from; const n = Math.round(beat2Seconds(b, vo) * fps); from += n; return { b, from: f, n }; });
  return (
    <AbsoluteFill style={{ background: "#f5f1e8" }}>
      {items.map(({ b, from, n }) => (
        <Sequence key={b.key} from={from} durationInFrames={n} name={b.key}>
          <Short2 b={b} vo={vo} clips={clips} />
          {vo[b.vo] && <Sequence from={Math.round(0.4 * fps)} layout="none"><Audio src={staticFile(vo[b.vo].file)} /></Sequence>}
        </Sequence>
      ))}
      {subtitles && items.map(({ b, from, n }) => {
        if (frame < from || frame >= from + n || !vo[b.vo]) return null;
        return <Subtitle key={b.key} chunks={chunks(vo[b.vo])} t={frame / fps - from / fps - 0.4} />;
      })}
    </AbsoluteFill>
  );
};

const metaShort: CalculateMetadataFunction<Props> = async ({ props }) => {
  const [vo, clips] = await Promise.all([
    fetch(staticFile("vo/manifest.json")).then((r) => r.json()) as Promise<Manifest>,
    fetch(staticFile("phone/clips/manifest.json")).then((r) => r.json()) as Promise<Clips>,
  ]);
  await fontsReady;
  const secs = BEATS2.reduce((s, b) => s + beat2Seconds(b, vo), 0);
  return { props: { ...props, vo, clips }, durationInFrames: Math.round(secs * FPS) };
};

export const ShortRoot: React.FC = () => (
  <Composition id="PehraShort" component={VideoShort} width={W} height={H} fps={FPS} durationInFrames={300}
    defaultProps={{ vo: {}, clips: {}, subtitles: true }} calculateMetadata={metaShort} />
);
