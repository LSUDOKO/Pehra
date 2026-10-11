// Act 1: the problem, told fully. Real numbers from docs/results and the live audit page.
import React from "react";
import { Audio, Img, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { C, FONT, MARGIN, W } from "../brand";
import { clamp01, countUp, ease, easeOut, fmt, rise, sp, SPRING_SOFT } from "../lib/motion";
import { at } from "../lib/vo";
import { Dot } from "../ui/Dot";
import { Card, Frame } from "../ui/Frame";
import { Illustration, Site } from "../ui/Media";
import { Body, Headline, Label, Source } from "../ui/Text";
import type { SceneProps } from "../timeline";

const ACT = "The problem";

export const Open: React.FC<SceneProps> = ({ track }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tBut = Math.round(at(track, "But", 3.4) * fps);
  return (
    <Frame>
      <Illustration src="gen/humid_street.png" x={900} y={0} w={1020} h={1080} zoom={1.08} focus={[0.5, 0.35]} />
      <div style={{ position: "absolute", left: MARGIN, top: 250, width: 720 }}>
        <Label delay={4} bg={C.saffron} color={C.ink}>India, every summer</Label>
        <div style={{ height: 26 }} />
        <Headline delay={8} size={84}>Heat is measured with a thermometer.</Headline>
        {frame > tBut && <Headline delay={tBut} size={84} color={C.saffron} style={{ marginTop: 18 }}>A body feels something else.</Headline>}
      </div>
      <Dot x={820} y={200} r={40} delay={0} />
    </Frame>
  );
};

export const Humidity: React.FC<SceneProps> = ({ track }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tHumid = Math.round(at(track, "humid", 2.6) * fps);
  const tSo = Math.round(at(track, "So", 6.2) * fps);
  const k = ease(frame, tHumid, tHumid + 40);
  return (
    <Frame act={ACT}>
      <Illustration src="gen/thermometer.png" x={MARGIN} y={160} w={820} h={760} radius={24} zoom={1.05} />
      <div style={{ position: "absolute", left: 1040, top: 180, width: 760 }}>
        <Headline delay={2} size={64}>Sweat is the body's cooling.</Headline>
        <Body delay={14} size={32} color={C.muted} style={{ marginTop: 22 }}>On a humid day sweat cannot dry, so the cooling stops.</Body>
        <div style={{ marginTop: 56, display: "flex", gap: 22 }}>
          {[["36 °C", "humid", C.red, "can hurt more"], ["42 °C", "dry", C.ink, "than this"]].map(([big, small, col, note], i) => {
            const kk = sp(frame, fps, tSo + i * 8);
            return (
              <div key={i} style={{ flex: 1, background: C.surface, border: `1.5px solid ${C.line}`, borderRadius: 22, padding: 30, opacity: clamp01(kk * 1.5), transform: `translateY(${(1 - kk) * 24}px)` }}>
                <div style={{ fontFamily: FONT, fontSize: 76, fontWeight: 800, color: col, letterSpacing: -3 }}>{big}</div>
                <div style={{ fontFamily: FONT, fontSize: 26, fontWeight: 700, color: C.ink, marginTop: 4 }}>{small} day</div>
                <div style={{ fontFamily: FONT, fontSize: 22, color: C.muted, marginTop: 10 }}>{note}</div>
              </div>
            );
          })}
        </div>
        <div style={{ marginTop: 34, height: 10, background: C.line, borderRadius: 5, overflow: "hidden" }}>
          <div style={{ width: `${easeOut(k) * 100}%`, height: "100%", background: C.saffron }} />
        </div>
        <Body delay={tHumid + 6} size={22} color={C.muted} style={{ marginTop: 12 }}>humidity rising → cooling falling</Body>
      </div>
    </Frame>
  );
};

export const Wbgt: React.FC<SceneProps> = ({ track }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t0 = Math.round(at(track, "combines", 3.6) * fps);
  const tIndia = Math.round(at(track, "India", 10.5) * fps);
  const parts = [["Temperature", "air"], ["Humidity", "wet bulb"], ["Sun", "black globe"], ["Wind", "cooling"]];
  const kSum = sp(frame, fps, t0 + 36, SPRING_SOFT);
  return (
    <Frame act={ACT}>
      <div style={{ position: "absolute", left: MARGIN, top: 170 }}>
        <Label delay={2}>Wet Bulb Globe Temperature</Label>
        <div style={{ height: 20 }} />
        <Headline delay={6} size={150} style={{ letterSpacing: -8 }}>WBGT</Headline>
        <Body delay={14} size={30} color={C.muted} maxWidth={760} style={{ marginTop: 10 }}>One number for what the body actually faces. Used by NIOSH, OSHA and many armies to decide when work must stop.</Body>
      </div>
      <div style={{ position: "absolute", left: 1000, top: 190, width: 800 }}>
        {parts.map(([a, b], i) => {
          const k = sp(frame, fps, t0 + i * 7);
          return (
            <div key={a} style={{ display: "flex", alignItems: "center", gap: 22, marginBottom: 18, opacity: clamp01(k * 1.5), transform: `translateX(${(1 - k) * 40}px)` }}>
              <div style={{ width: 18, height: 18, borderRadius: 9, background: C.saffron, boxShadow: `0 0 0 3px ${C.ink}` }} />
              <div style={{ fontFamily: FONT, fontSize: 44, fontWeight: 700, color: C.ink, width: 300 }}>{a}</div>
              <div style={{ fontFamily: FONT, fontSize: 24, color: C.muted }}>{b}</div>
            </div>
          );
        })}
        <div style={{ marginTop: 10, height: 2, background: C.ink, width: 600, transform: `scaleX(${kSum})`, transformOrigin: "left" }} />
        <div style={{ marginTop: 22, fontFamily: FONT, fontSize: 36, fontWeight: 800, color: C.ink, opacity: kSum }}>= WBGT, in °C</div>
      </div>
      {frame > tIndia && (
        <Card x={1000} y={620} w={800} delay={tIndia} style={{ background: C.ink, border: "none" }}>
          <div style={{ fontFamily: FONT, fontSize: 24, fontWeight: 700, color: C.saffron, letterSpacing: 2, textTransform: "uppercase" }}>India's public heat alerts</div>
          <div style={{ fontFamily: FONT, fontSize: 40, fontWeight: 700, color: C.surface, marginTop: 10, lineHeight: 1.2 }}>Temperature alone, by district, against a seasonal normal.</div>
        </Card>
      )}
      <Source delay={30}>NIOSH 2016 criteria; OSHA Technical Manual; IMD heatwave criteria (departure from normal). See the model card.</Source>
    </Frame>
  );
};

export const Kharghar: React.FC<SceneProps> = ({ track }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tMax = Math.round(at(track, "maximum", 7.5) * fps);
  const tRule = Math.round(at(track, "Under", 11.0) * fps);
  const tNo = Math.round(at(track, "No", 14.5, 1) * fps);
  const kStamp = sp(frame, fps, tNo, { damping: 14, stiffness: 260, mass: 0.8 });
  return (
    <Frame act={ACT}>
      <Illustration src="gen/open_ground.png" x={960} y={0} w={960} h={1080} zoom={1.08} focus={[0.5, 0.4]} />
      <div style={{ position: "absolute", left: MARGIN, top: 170, width: 760 }}>
        <Label delay={2} bg={C.red}>16 April 2023</Label>
        <div style={{ height: 18 }} />
        <Headline delay={6} size={62}>Kharghar, Navi Mumbai</Headline>
        <Body delay={16} size={28} color={C.muted} style={{ marginTop: 10 }}>An open-air event at noon. People died of heatstroke.</Body>
        {frame > tMax && (
          <div style={{ marginTop: 34, background: C.surface, border: `1.5px solid ${C.line}`, borderRadius: 22, padding: "24px 30px", ...rise(frame, fps, tMax) }}>
            <div style={{ fontFamily: FONT, fontSize: 22, color: C.muted, fontWeight: 600 }}>Maximum temperature that day (ERA5)</div>
            <div style={{ fontFamily: FONT, fontSize: 92, fontWeight: 800, color: C.ink, letterSpacing: -4, lineHeight: 1 }}>38.8 °C</div>
            <div style={{ fontFamily: FONT, fontSize: 24, color: C.muted, marginTop: 8 }}>+3.5 °C above the 1991–2020 normal</div>
          </div>
        )}
        {frame > tRule && (
          <Body delay={tRule} size={28} color={C.ink} style={{ marginTop: 26 }}>Coastal heatwave rule: 37 °C or more <b>and</b> 4.5 °C above normal.</Body>
        )}
        {frame > tNo && (
          <div style={{ marginTop: 26, display: "inline-block", border: `5px solid ${C.red}`, color: C.red, borderRadius: 12, padding: "10px 26px", fontFamily: FONT, fontWeight: 800, fontSize: 52, letterSpacing: 1, transform: `rotate(-4deg) scale(${0.7 + 0.3 * kStamp})`, opacity: clamp01(kStamp * 2) }}>NO HEATWAVE · NO ALERT</div>
        )}
      </div>
      <Source delay={40} style={{ maxWidth: 760 }}>Replay on ERA5 reanalysis (Open-Meteo archive, CC BY 4.0), grid cell 19.02 N 73.05 E. The IMD rule is recreated, not IMD's record.</Source>
    </Frame>
  );
};

const HOURS = [[6, 21.8], [7, 23.7], [8, 25.9], [9, 28.1], [10, 29.2], [11, 30.6], [12, 30.8], [13, 30.5], [14, 29.3], [15, 28.7], [16, 28.3], [17, 27.4], [18, 26.4], [19, 25.2]];
const LIMIT = 28.2;

export const KharghatChart: React.FC<SceneProps> = ({ track }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tBars = Math.round(at(track, "crossed", 3.2) * fps) - 20;
  const tLimit = Math.round(at(track, "limit", 4.2) * fps);
  const tPeak = Math.round(at(track, "peaking", 9.5) * fps);
  const tInv = Math.round(at(track, "invisible", 13.5) * fps);
  const x0 = MARGIN + 90, y0 = 820, pw = W - 2 * MARGIN - 120, ph = 520;
  const vmin = 20, vmax = 33;
  const vy = (v: number) => y0 - ((v - vmin) / (vmax - vmin)) * ph;
  const bw = pw / HOURS.length;
  const kLim = sp(frame, fps, tLimit, SPRING_SOFT);
  return (
    <Frame act={ACT}>
      <div style={{ position: "absolute", left: MARGIN, top: 160 }}>
        <Headline delay={2} size={54}>The same day, measured as WBGT in the sun</Headline>
        <Body delay={10} size={24} color={C.muted}>Hour by hour, 16 April 2023, Kharghar · °C</Body>
      </div>
      {[22, 26, 30].map((v) => (
        <div key={v} style={{ position: "absolute", left: MARGIN, top: vy(v) - 14, fontFamily: FONT, fontSize: 20, color: C.muted, width: 70, textAlign: "right" }}>{v}</div>
      ))}
      {HOURS.map(([h, v], i) => {
        const k = sp(frame, fps, tBars + i * 3, { damping: 20, stiffness: 160, mass: 0.9 });
        const top = vy(vmin + (v - vmin) * k);
        const over = v > LIMIT && k > 0.95;
        return (
          <React.Fragment key={h}>
            <div style={{ position: "absolute", left: x0 + i * bw + 8, top, width: bw - 16, height: y0 - top, borderRadius: 8, background: over ? C.red : C.line }} />
            <div style={{ position: "absolute", left: x0 + i * bw, top: y0 + 12, width: bw, textAlign: "center", fontFamily: FONT, fontSize: 20, color: C.muted }}>{h}:00</div>
          </React.Fragment>
        );
      })}
      <div style={{ position: "absolute", left: x0, top: vy(LIMIT) - 2, width: pw * kLim, height: 4, background: C.ink }} />
      <div style={{ position: "absolute", left: x0 + 8, top: vy(LIMIT) - 50, fontFamily: FONT, fontSize: 22, fontWeight: 700, color: C.surface, background: C.ink, padding: "6px 14px", borderRadius: 8, opacity: kLim }}>28.2 °C · NIOSH limit, moderate work</div>
      {frame > tPeak && (
        <div style={{ position: "absolute", left: x0 + 6 * bw + bw / 2 - 120, top: vy(30.8) - 70, width: 240, textAlign: "center", fontFamily: FONT, fontSize: 24, fontWeight: 800, color: C.red, ...rise(frame, fps, tPeak, 16) }}>peak 30.8 °C at 12:00</div>
      )}
      {frame > tInv && (
        <div style={{ position: "absolute", right: MARGIN, top: 176, fontFamily: FONT, fontSize: 40, fontWeight: 800, color: C.ink, ...rise(frame, fps, tInv) }}>Real. <span style={{ color: C.saffron }}>Invisible.</span></div>
      )}
      <Source delay={40}>WBGT by the Liljegren method (thermofeel). Our calculation; no claim that anyone would have been saved.</Source>
    </Frame>
  );
};

const CITIES: [string, number][] = [["Kolkata", 676], ["Bhubaneswar", 656], ["Patna", 571], ["Chennai", 512], ["Lucknow", 460], ["Guwahati", 342], ["Delhi", 341], ["Ahmedabad", 338], ["Kharghar", 223], ["Jaipur", 136], ["Nagpur", 112], ["Hyderabad", 5]];

export const Audit: React.FC<SceneProps> = ({ track }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tNum = Math.round(at(track, "4,372", 7.0) * fps);
  const t97 = Math.round(at(track, "97", 12.5) * fps);
  const t2327 = Math.round(at(track, "2,327", 15.0) * fps);
  const tPage = Math.round(at(track, "published", 21.0) * fps);
  const n = countUp(frame, fps, tNum, 4372, 1.6);
  const showPage = frame > tPage;
  return (
    <Frame act={ACT}>
      <div style={{ position: "absolute", left: MARGIN, top: 170, width: 820 }}>
        <Label delay={2}>The Pehra audit · 12 cities · 2021–2025</Label>
        <div style={{ fontFamily: FONT, fontSize: 200, fontWeight: 800, color: C.green, letterSpacing: -10, lineHeight: 1, marginTop: 26, opacity: clamp01((frame - tNum) / 8) }}>{fmt(n)}</div>
        <Body delay={tNum + 10} size={34} weight={700}>city-days over the WBGT work limit, no heatwave declared</Body>
        <div style={{ marginTop: 30, display: "flex", flexDirection: "column", gap: 14 }}>
          {frame > t97 && <Label delay={t97} bg={C.saffron} color={C.ink} size={24}>97% of all such days</Label>}
          {frame > t2327 && <Label delay={t2327} bg={C.ink} size={24}>2,327 outside March–June, when bulletins do not run</Label>}
        </div>
      </div>
      {!showPage && (
        <div style={{ position: "absolute", left: 1060, top: 190, width: 740 }}>
          {CITIES.map(([city, v], i) => {
            const k = sp(frame, fps, tNum + 10 + i * 4);
            return (
              <div key={city} style={{ display: "flex", alignItems: "center", gap: 16, height: 46, opacity: clamp01(k * 1.5) }}>
                <div style={{ width: 150, textAlign: "right", fontFamily: FONT, fontSize: 22, fontWeight: 600, color: C.ink }}>{city}</div>
                <div style={{ width: (v / 676) * 480 * k, height: 20, borderRadius: 10, background: C.green }} />
                <div style={{ fontFamily: FONT, fontSize: 22, color: C.muted }}>{v}</div>
              </div>
            );
          })}
        </div>
      )}
      {showPage && (
        <Site src="site/audit.png" imgW={1905} imgH={1918} x={1000} y={150} w={800} h={740} delay={tPage}
          view={{ x: 530, y: 10, w: 860 }}
          highlights={[{ x: 540, y: 215, w: 320, h: 110, at: tPage / fps + 0.6, label: "live audit page" }, { x: 540, y: 600, w: 830, h: 210, at: tPage / fps + 1.8, label: "every caveat" }]} />
      )}
      <Source delay={30}>pehra audit page · ERA5 via Open-Meteo (CC BY 4.0) · shade WBGT, 06–19 IST · a minimum: ERA5 (~25 km) smooths humid extremes</Source>
    </Frame>
  );
};

export const Water: React.FC<SceneProps> = ({ track }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tRain = Math.round(at(track, "90", 2.2) * fps);
  const tNight = Math.round(at(track, "68", 4.0) * fps);
  const tOne = Math.round(at(track, "one", 7.0) * fps);
  return (
    <Frame act={ACT} dark>
      <div style={{ position: "absolute", left: MARGIN, top: 200, display: "flex", gap: 40 }}>
        {[["90", "days of heavy rain", "IMD 'heavy': 64.5 mm or more in a day", tRain], ["68", "warm nights", "the body cannot recover after a hot day", tNight]].map(([big, a, b, t], i) => (
          <Card key={i} x={0} y={0} w={800} delay={t as number} dark style={{ position: "relative" }}>
            <div style={{ fontFamily: FONT, fontSize: 150, fontWeight: 800, color: C.saffron, letterSpacing: -6, lineHeight: 1 }}>{big}</div>
            <div style={{ fontFamily: FONT, fontSize: 40, fontWeight: 700, color: C.surface, marginTop: 10 }}>{a}</div>
            <div style={{ fontFamily: FONT, fontSize: 24, color: "rgba(255,253,248,0.7)", marginTop: 10 }}>{b}</div>
          </Card>
        ))}
      </div>
      {frame > tOne && <div style={{ position: "absolute", left: MARGIN, top: 720 }}><Headline delay={tOne} size={72} color={C.surface}>Heat and water are one problem.</Headline></div>}
      <Source delay={20} style={{ color: "rgba(255,253,248,0.6)" }}>Same 12 cities, 2021–2025, ERA5 at one grid cell per city. Warm nights by the recreated IMD rule.</Source>
    </Frame>
  );
};
