"""Build the demo video: animated scenes (PIL), Amazon Polly voice-over, burned-in subtitles, ffmpeg mux.

    uv run python scripts/video/cut_characters.py          # once: transparent character poses
    uv run python scripts/video/build_video.py             # out/video/pehra_demo.mp4 (+ .srt)
    uv run python scripts/video/build_video.py --stills    # out/video/stills/<scene>_<t>.jpg, no encode
    uv run python scripts/video/build_video.py --only aws  # one scene, out/video/preview_aws.mp4

Real footage is used when present (or passed): out/video/wokwi.mp4, out/video/twin.mp4, out/video/phone.mp4
(scrcpy --record out/video/phone.mp4). Without it the scenes fall back to stills and a recreated chat.
"""

import argparse
import bisect
import hashlib
import json
import subprocess
import sys
import wave
from functools import lru_cache
from multiprocessing import Pool
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from kit import FPS, WHITE, H, W, card, ease_in_out, text, text_w, wrap  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from scenes import PEOPLE, Cue, Scene, timeline, twin_overlay  # noqa: E402

OUT = Path("out/video")
VO_DIR = OUT / "vo"
VOICE = "Kajal"
LEAD = {"default": 0.55, "person": 0.35}
TAIL = {"default": 0.7, "person": 0.35}
TR = 0.5            # wipe between scenes
MAX_TOTAL = 178.0   # the submission limit is 3:00

TL: list[Scene] = []
STARTS: list[float] = []
SUBS: list[tuple[float, float, str]] = []
TOTAL = 0.0


# ---------- voice-over ----------
def synth(text_: str, lang: str = "en-IN") -> tuple[Path, float, list[tuple[float, str]]]:
    """Polly neural voice + word marks, cached by content hash."""
    import boto3
    VO_DIR.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha1(f"{VOICE}|{lang}|{text_}".encode()).hexdigest()[:16]
    mp3, marks = VO_DIR / f"{h}.mp3", VO_DIR / f"{h}.json"
    if not (mp3.exists() and marks.exists()):
        p = boto3.client("polly", region_name="ap-south-1")
        kw = dict(Text=text_, VoiceId=VOICE, Engine="neural", LanguageCode=lang)
        r = p.synthesize_speech(OutputFormat="mp3", SampleRate="24000", **kw)
        mp3.write_bytes(r["AudioStream"].read())
        m = p.synthesize_speech(OutputFormat="json", SpeechMarkTypes=["word"], **kw)
        marks.write_bytes(m["AudioStream"].read())
    words = [(j["time"] / 1000, j["value"], j["start"], j["end"])
             for j in map(json.loads, marks.read_text().splitlines()) if j]
    return mp3, probe_duration(mp3), words


def probe_duration(p: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def probe_video(p: Path) -> tuple[int, int, float]:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height:format=duration", "-of", "json", str(p)],
                         capture_output=True, text=True, check=True).stdout
    j = json.loads(out)
    return j["streams"][0]["width"], j["streams"][0]["height"], float(j["format"]["duration"])


def chunks(words: list[tuple], text_: str, end: float) -> list[tuple[float, float, str]]:
    """Subtitle chunks cut from the original text (Polly char offsets): break at sentence ends,
    at commas once long enough, and at ~58 characters."""
    raw = text_.encode()
    out, first = [], None
    for i, (t, _w, a, b) in enumerate(words):
        if first is None:
            first = (t, a)
        nxt_a = words[i + 1][2] if i + 1 < len(words) else len(raw)
        tail = raw[b:nxt_a].decode().strip()
        seg = raw[first[1]:b].decode() + tail
        last = i == len(words) - 1
        if last or tail[:1] in (".", "?", "!") or (tail[:1] == "," and len(seg) > 28) or len(seg) > 54:
            t1 = words[i + 1][0] if not last else end
            out.append((first[0], t1, seg.strip().rstrip(",")))
            first = None
    return out


# ---------- frames ----------
def lead_of(s: Scene) -> str:
    return "person" if s.key in {p.key for p in PEOPLE} else "default"


@lru_cache(maxsize=4)
def last_frame(i: int) -> Image.Image:
    s = TL[i]
    return s.render(s.dur, s.dur, s.cue)


def wipe(prev: Image.Image, new: Image.Image, k: float, color: tuple) -> Image.Image:
    k = ease_in_out(k)
    edge = -300 + k * (W + 600)
    skew = 260
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon([(0, 0), (edge + skew, 0), (edge - skew, H), (0, H)], fill=255)
    out = Image.composite(new, prev, m)
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(band).polygon([(edge + skew, 0), (edge + skew + 70, 0), (edge - skew + 70, H), (edge - skew, H)],
                                 fill=color + (255,))
    out.alpha_composite(band)
    return out


def subtitle(c: Image.Image, s: str) -> None:
    lines = wrap(s, 40, 1440, "Medium")[:2]
    lh = 58
    h = 28 + lh * len(lines)
    w = int(max(text_w(ln, 40, "Medium") for ln in lines)) + 72
    x, y = (W - w) / 2, H - 46 - h
    card(c, x, y, w, h, 22, (22, 14, 10, 178), 1.0, False)
    for i, ln in enumerate(lines):
        text(c, ln, W / 2, y + 12 + i * lh, 40, "Medium", WHITE, "m")


def frame(i: int) -> bytes:
    t = i / FPS
    si = max(0, bisect.bisect_right(STARTS, t) - 1)
    s = TL[si]
    lt = t - s.start
    img = s.render(lt, s.dur, s.cue)
    if si > 0 and lt < TR:
        img = wipe(last_frame(si - 1), img, lt / TR, s.accent)
    for a, b, txt in SUBS:
        if a <= t < b:
            subtitle(img, txt)
            break
    k = min(1.0, t / 0.6, (TOTAL - t) / 1.0)
    if k < 1:
        img = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), img, max(0.0, k))
    return img.convert("RGB").tobytes()


# ---------- music ----------
def music(path: Path, dur: float, sr: int = 44100) -> None:
    """A soft generated pad + pentatonic plucks (D major), so the mix has no third-party audio."""
    n = int(dur * sr)
    t = np.arange(n) / sr
    out = np.zeros((n, 2))
    bpm = 84
    beat = 60 / bpm
    chords = [[62, 66, 69], [59, 62, 66], [55, 59, 62], [57, 61, 64]]  # D Bm G A
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)  # noqa: E731
    clen = 8 * beat
    for ci in range(int(dur / clen) + 1):
        a, b = ci * clen, min(dur, (ci + 1) * clen + 1.5)
        s0, s1 = int(a * sr), int(b * sr)
        if s0 >= n:
            break
        tt = t[s0:s1] - a
        env = np.minimum(1, tt / 1.6) * np.minimum(1, np.maximum(0, (b - a - tt) / 1.6))
        for m in chords[ci % 4]:
            for det, pan in ((0.999, 0.3), (1.0015, 0.7)):
                w = np.sin(2 * np.pi * hz(m - 12) * det * tt) * 0.05 * env
                out[s0:s1, 0] += w * (1 - pan)
                out[s0:s1, 1] += w * pan
        root = chords[ci % 4][0] - 24
        out[s0:s1] += (np.sin(2 * np.pi * hz(root) * tt) * 0.06 * env)[:, None]
    rng = np.random.default_rng(3)
    scale = [62, 64, 66, 69, 71, 74, 76, 78]
    step = beat / 2
    for k in range(int(dur / step)):
        if rng.random() < 0.45:
            continue
        m = scale[rng.integers(0, len(scale))]
        s0 = int(k * step * sr)
        ln = min(int(1.6 * sr), n - s0)
        if ln <= 0:
            break
        tt = np.arange(ln) / sr
        f = hz(m)
        w = (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(4 * np.pi * f * tt) + 0.15 * np.sin(6 * np.pi * f * tt))
        w *= np.exp(-tt * 3.2) * np.minimum(1, tt / 0.004) * 0.035
        pan = 0.25 if k % 2 else 0.75
        out[s0:s0 + ln, 0] += w * (1 - pan)
        out[s0:s0 + ln, 1] += w * pan
    out /= max(1e-6, np.abs(out).max()) / 0.6
    with wave.open(str(path), "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes((out * 32767).astype(np.int16).tobytes())


# ---------- build ----------
def fmt_srt(t: float) -> str:
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def plan(clips: dict) -> list[dict]:
    """Voice-over, scene durations, start times and subtitles. Returns the VO tracks."""
    global TOTAL
    TL[:] = timeline(clips)
    tracks = []
    for s in TL:
        mp3, vdur, words = synth(s.vo, s.lang)
        lead, tail = LEAD[lead_of(s)], TAIL[lead_of(s)]
        s.cue = Cue([(w[0], w[1]) for w in words], lead, vdur)
        s.dur = max(s.min_dur, lead + vdur + tail)
        tracks.append({"mp3": mp3, "lead": lead, "words": words, "vdur": vdur})
    over = sum(s.dur for s in TL) - MAX_TOTAL
    if over > 0:  # trim the slack beyond each voice-over, proportionally
        slack = [max(0.0, s.dur - (s.cue.end + 0.3)) for s in TL]
        k = min(1.0, over / max(1e-6, sum(slack)))
        for s, sl in zip(TL, slack):
            s.dur -= sl * k
    t = 0.0
    STARTS.clear()
    SUBS.clear()
    for s, tr in zip(TL, tracks):
        s.dur = round(s.dur * FPS) / FPS
        s.start = t
        STARTS.append(t)
        for a, b, txt in chunks(tr["words"], s.vo, tr["vdur"] + 0.25):
            SUBS.append((t + tr["lead"] + a, t + tr["lead"] + min(b, tr["vdur"] + 0.25), txt))
        tr["start"] = t
        t += s.dur
    TOTAL = t
    for s in TL:
        if s.key == "sitebox" and "twin" in clips:
            twin_overlay(s)
    return tracks


def encode(n0: int, n1: int, dst: Path, workers: int) -> None:
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           str(dst)]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(workers) as pool:
        for k, b in enumerate(pool.imap(frame, range(n0, n1), chunksize=6)):
            ff.stdin.write(b)
            if k % 300 == 0:
                print(f"  frame {n0 + k}/{n1}", flush=True)
    ff.stdin.close()
    if ff.wait():
        raise SystemExit("ffmpeg failed")


def overlay_filters(clips: dict, t_off: float = 0.0) -> tuple[list[str], list[str]]:
    """ffmpeg inputs + filter graph that place real footage into the scene panels."""
    inputs, graph, last, idx = [], [], "[0:v]", 1
    for s in TL:
        for key, (bx, by, bw, bh), a, b in s.overlays:
            path, cw, ch, cdur = clips[key]
            t0 = s.start + a - t_off
            t1 = s.start + (b if b is not None else s.dur) - t_off
            k = min(bw / cw, bh / ch)
            w, h = int(cw * k) // 2 * 2, int(ch * k) // 2 * 2
            x, y = bx + (bw - w) // 2, by + (bh - h) // 2
            inputs += ["-stream_loop", "-1", "-i", str(path)] if key != "phone" else ["-i", str(path)]
            graph.append(f"[{idx}:v]trim=duration={t1 - t0:.3f},setpts=PTS-STARTPTS+{max(0, t0):.3f}/TB,"
                         f"scale={w}:{h},fps={FPS}[c{idx}]")
            graph.append(f"{last}[c{idx}]overlay={x}:{y}:enable='between(t,{t0:.3f},{t1:.3f})':eof_action=pass"
                         f"[v{idx}]")
            last, idx = f"[v{idx}]", idx + 1
    return inputs, graph + ([f"{last}null[vout]"] if graph else [])


def mix_audio(tracks: list[dict], dst: Path, with_music: bool, phone: tuple | None) -> None:
    inputs, parts = [], []
    for i, tr in enumerate(tracks):
        inputs += ["-i", str(tr["mp3"])]
        ms = int((tr["start"] + tr["lead"]) * 1000)
        parts.append(f"[{i}:a]aresample=44100,adelay={ms}|{ms},volume=1.0[a{i}]")
    n = len(tracks)
    labels = "".join(f"[a{i}]" for i in range(n))
    graph = parts + [f"{labels}amix=inputs={n}:normalize=0,apad,atrim=0:{TOTAL:.3f}[vo]"]
    extra = n
    if phone:
        start, path = phone
        inputs += ["-i", str(path)]
        ms = int(start * 1000)
        graph.append(f"[{extra}:a]aresample=44100,adelay={ms}|{ms},volume=0.9,apad,atrim=0:{TOTAL:.3f}[ph]")
        graph.append("[vo][ph]amix=inputs=2:normalize=0[vo2]")
        extra += 1
        vo = "[vo2]"
    else:
        vo = "[vo]"
    if with_music:
        mpath = OUT / "music.wav"
        music(mpath, TOTAL + 1)
        inputs += ["-i", str(mpath)]
        graph.append(f"{vo}asplit=2[vok][vosc]")
        graph.append(f"[{extra}:a]atrim=0:{TOTAL:.3f},volume=0.33,afade=t=in:d=2,afade=t=out:st={TOTAL - 3:.3f}:d=3[m]")
        graph.append("[m][vosc]sidechaincompress=threshold=0.03:ratio=6:attack=40:release=400[md]")
        graph.append("[vok][md]amix=inputs=2:normalize=0,alimiter=limit=0.95[aout]")
    else:
        graph.append(f"{vo}alimiter=limit=0.95[aout]")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(graph), "-map", "[aout]",
           "-c:a", "aac", "-b:a", "192k", str(dst)]
    subprocess.run(cmd, check=True)


def find_clips(args) -> dict:
    clips = {}
    for key in ("wokwi", "twin", "phone"):
        p = Path(getattr(args, key) or OUT / f"{key}.mp4")
        if p.exists() and p.stat().st_size > 10_000:
            w, h, d = probe_video(p)
            clips[key] = (p, w, h, d)
    return clips


def has_audio(p: Path) -> bool:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                          "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout
    return bool(out.strip())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wokwi")
    ap.add_argument("--twin")
    ap.add_argument("--phone")
    ap.add_argument("--no-music", action="store_true")
    ap.add_argument("--stills", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--out", default=str(OUT / "pehra_demo.mp4"))
    args = ap.parse_args()
    clips = find_clips(args)
    tracks = plan(clips)
    print(f"{len(TL)} scenes, {TOTAL:.1f} s, footage: {sorted(clips) or 'none'}")
    for s in TL:
        print(f"  {s.key:10s} {s.start:6.1f}  {s.dur:5.1f} s  (vo {s.cue.vo_dur:4.1f})")
    if args.stills:
        d = OUT / "stills"
        d.mkdir(parents=True, exist_ok=True)
        for s in TL:
            if args.only and s.key != args.only:
                continue
            for k in (0.25, 0.55, 0.9):
                lt = s.dur * k
                img = s.render(lt, s.dur, s.cue)
                for a, b, txt in SUBS:
                    if a <= s.start + lt < b:
                        subtitle(img, txt)
                img.convert("RGB").save(d / f"{s.key}_{int(k * 100)}.jpg", quality=86)
        print(f"stills in {d}")
        return
    tmp = OUT / "_video.mp4"
    if args.only:
        s = next(s for s in TL if s.key == args.only)
        n0, n1 = int(s.start * FPS), int((s.start + s.dur) * FPS)
        encode(n0, n1, tmp, args.workers)
        out = OUT / f"preview_{s.key}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp), "-c", "copy", str(out)], check=True)
        print(out)
        return
    encode(0, int(round(TOTAL * FPS)), tmp, args.workers)
    inputs, graph = overlay_filters(clips)
    vid = tmp
    if graph:
        vid = OUT / "_video_ov.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(tmp), *inputs, "-filter_complex",
                        ";".join(graph), "-map", "[vout]", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                        "-pix_fmt", "yuv420p", "-t", f"{TOTAL:.3f}", str(vid)], check=True)
    aud = OUT / "_audio.m4a"
    phone = None
    if "phone" in clips and has_audio(clips["phone"][0]):
        s = next(s for s in TL if s.key == "phone")
        phone = (s.start + 0.5, clips["phone"][0])
    mix_audio(tracks, aud, not args.no_music, phone)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(vid), "-i", str(aud), "-map", "0:v", "-map",
                    "1:a", "-c:v", "copy", "-c:a", "copy", "-movflags", "+faststart", "-shortest", args.out],
                   check=True)
    srt = Path(args.out).with_suffix(".srt")
    srt.write_text("\n".join(f"{i}\n{fmt_srt(a)} --> {fmt_srt(b)}\n{txt}\n" for i, (a, b, txt) in
                             enumerate(SUBS, 1)))
    for p in (tmp, OUT / "_video_ov.mp4", aud):
        p.unlink(missing_ok=True)
    print(f"{args.out}  {probe_duration(Path(args.out)):.1f} s  + {srt}")


if __name__ == "__main__":
    main()
