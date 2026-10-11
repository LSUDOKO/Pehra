"""Cut the raw phone recording (scrcpy) into one clip per WhatsApp feature for build_video.py.

    uv run python scripts/video/phone_cut.py [--src out/video/raw/phone_1.mp4] [--only wa_plan]
Writes out/video/phone/<key>.mp4 and out/video/phone/manifest.json.

Times are seconds into the raw recording. Waiting stretches are sped up (the video says so on screen).
Private bits are blurred: the owner's phone number while it is typed and on screen. Calls are not
captured by screen recording, so each call's audio is the same Polly MP3 the call played (made from
the same template, see the CALLS table), placed where the call played it.
"""

import argparse
import json
import subprocess
from pathlib import Path

OUT = Path("out/video/phone")
FIX = "null"  # the source is first remuxed with bt709 tags (scrcpy writes YCgCo), see bt709()

# key: pieces [(t0, t1, speed)], blur boxes [(t0, t1, x, y, w, h)] in source px, keep the recording's
# own audio (voice note playback), calls [(source time the Hindi audio starts, mp3 name)],
# beats [(source time, on-screen step)]
NUMBER = [(1447, 1453.5, 20, 850, 600, 160), (1452, 1456.5, 200, 1270, 520, 100), (1453, 1491.5, 390, 1090, 320, 90), (1491, 1566, 390, 180, 320, 90)]
SEGMENTS = {
    "wa_hi": {"beats": [(36, 'hi sent'), (44, 'privacy note: what Pehra keeps'), (52, 'two buttons'), (60, 'tap: Mere aur parivar ke liye')], "pieces": [(34, 64, 1.25)]},
    "wa_profile": {"beats": [(66, 'city: Mumbai'), (100, 'elderly 1 · under-5 1'), (118, 'pregnant: Haan · illness: 0'), (138, 'outdoor work: Haan')], "pieces": [(64, 150, 3.0)]},
    "wa_today": {"beats": [(152, "today's family plan arrives")], "pieces": [(150, 166, 1.0)]},
    "wa_paani": {"beats": [(800, 'paani Connaught Place'), (806, 'nearest water: 190 m, map links')], "pieces": [(798, 822, 1.0)]},
    "wa_register": {"beats": [(683, '/register Ramesh Tower, Kharghar'), (691, 'type: Construction site')], "pieces": [(679, 698, 1.0)]},
    "wa_crew": {"beats": [(699, 'crew typed in Hindi'), (705, 'read back, tap: Haan, sahi'), (713, '/call_on')], "pieces": [(697, 723, 1.25)]},
    "wa_plan": {"beats": [(717, 'plan'), (727, "tomorrow's plan + buttons"), (748, 'Hindi voice note playing'), (770, 'Approve: saved to the record')], "pieces": [(716, 746, 1.25), (746, 780, 1.0)], "audio": True},
    "wa_links": {"beats": [(825, 'links: QR page + poster')], "pieces": [(822, 848, 1.5)]},
    "wa_worker": {"beats": [(850, 'worker page opens, no app'), (865, 'Aaram shuru: break logged'), (883, 'Chakkar: fixed first aid'), (888, 'supervisor alerted on WhatsApp'), (892, "supervisor's phone rings")], "pieces": [(848, 900, 1.25)]},
    "wa_alert": {"beats": [(978, "the alert in the supervisor's chat")], "pieces": [(976, 990, 1.0)]},
    "wa_call": {"beats": [(1256, 'call: a test call'), (1283, 'phone rings'), (1287, 'answered (trial notice first)'), (1297, 'Hindi message plays')], "pieces": [(1252, 1284, 2.0), (1284, 1315, 1.0)], "calls": [(1297.0, "call_test")]},
    "wa_agent": {"beats": [(1395, 'question typed'), (1399, 'Soch raha hoon...'), (1411, "answer from the plan's tools")], "pieces": [(1392, 1426, 1.25)]},
    "wa_family": {"beats": [(1448, '/family_call + number (blurred)'), (1456, 'family call on'), (1494, "today's family plan sent"), (1503, "Dadi's phone rings"), (1510, 'Hindi family call plays')], "pieces": [(1444, 1500, 1.5), (1500, 1550, 1.0)], "blur": NUMBER, "calls": [(1510.5, "call_family")]},
    "wa_box": {"beats": [(1561, '/device box'), (1567, 'box registered + twin link'), (1600, 'alerts: hotter than forecast, tank low')], "pieces": [(1556, 1612, 1.25)], "blur": NUMBER},
    "wa_twin": {"beats": [(1620, 'twin: LIVE · AWS IoT Core'), (1636, 'tank refilling, pump on')], "pieces": [(1616, 1656, 1.0)]},
    "wa_sos": {"beats": [(1657, 'SOS pressed on the box'), (1661, 'WhatsApp SOS alert'), (1666, 'Hindi SOS call'), (1712, 'the SOS message in WhatsApp')], "pieces": [(1656, 1706, 1.0), (1706, 1738, 1.25)], "calls": [(1674.5, "call_symptom")]},
    "wa_override": {"beats": [(1740, 'plan'), (1760, 'Override'), (1782, 'Dheela: looser'), (1800, 'reason typed'), (1822, 'saved with the reason')], "pieces": [(1736, 1836, 2.0)]},
}


def run(cmd: list[str]) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def bt709(src: Path) -> Path:
    """Lossless remux that rewrites the H.264 colour tags; ffmpeg cannot convert scrcpy's YCgCo tag."""
    out = src.with_name(src.stem + "_bt709.mp4")
    if not out.exists():
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-c", "copy", "-bsf:v",
             "h264_metadata=matrix_coefficients=1:colour_primaries=1:transfer_characteristics=1", str(out)])
    return out


def duration(p: Path) -> float:
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]))


def twice(mp3: Path) -> Path:
    """The call TwiML plays the audio, pauses 1 s, and plays it again."""
    out = mp3.with_name(mp3.stem + "_x2.wav")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3), "-filter_complex",
         "[0:a]aresample=44100,asplit[a][b];aevalsrc=0:d=1:s=44100[s];[a][s][b]concat=n=3:v=0:a=1", str(out)])
    return out


def cut(src: Path, key: str, seg: dict) -> dict:
    inputs, chains, labels = [], [], []
    keep_audio = seg.get("audio", False)
    for i, (t0, t1, speed) in enumerate(seg["pieces"]):
        inputs += ["-ss", str(t0), "-to", str(t1), "-i", str(src)]
        f = f"[{i}:v]{FIX}"
        for j, (b0, b1, x, y, w, h) in enumerate(b for b in seg.get("blur", []) if b[1] > t0 and b[0] < t1):
            f += (f"[v{i}_{j}];[v{i}_{j}]split[m{i}_{j}][c{i}_{j}];[c{i}_{j}]crop={w}:{h}:{x}:{y},boxblur=18:3"
                  f"[bl{i}_{j}];[m{i}_{j}][bl{i}_{j}]overlay={x}:{y}:enable='between(t,{b0 - t0},{b1 - t0})'")
        f += f",setpts=(PTS-STARTPTS)/{speed},fps=30,format=yuv420p[v{i}]"
        chains.append(f)
        if keep_audio:
            a = f"[{i}:a]asetpts=PTS-STARTPTS" + (f",atempo={speed}" if speed != 1 else "") + f"[a{i}]"
            chains.append(a)
            labels.append(f"[v{i}][a{i}]")
        else:
            labels.append(f"[v{i}]")
    n = len(seg["pieces"])
    chains.append("".join(labels) + f"concat=n={n}:v=1:a={1 if keep_audio else 0}" + ("[v][a]" if keep_audio else "[v]"))
    out = OUT / f"{key}.mp4"
    maps = ["-map", "[v]"] + (["-map", "[a]", "-c:a", "aac", "-b:a", "160k"] if keep_audio else ["-an"])
    run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(chains), *maps,
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-colorspace", "bt709", "-color_primaries", "bt709",
         "-color_trc", "bt709", str(out)])
    calls = []
    for t_src, name in seg.get("calls", []):
        acc = clip_time(seg, t_src)
        if acc is not None:
            calls.append({"at": round(acc, 3), "audio": str(twice(OUT / f"{name}.mp3"))})
    beats = [{"at": round(clip_time(seg, max(t, seg["pieces"][0][0])), 2), "text": txt}
             for t, txt in seg.get("beats", []) if clip_time(seg, max(t, seg["pieces"][0][0])) is not None]
    speeds = sorted({p[2] for p in seg["pieces"]})
    return {"path": str(out), "dur": round(duration(out), 3), "audio": keep_audio, "calls": calls,
            "beats": beats, "speed": max(speeds)}


def clip_time(seg: dict, t_src: float) -> float | None:
    """Map a time in the raw recording to the cut clip's timeline (pieces are sped up separately)."""
    rel = 0.0
    for t0, t1, speed in seg["pieces"]:
        if t0 <= t_src < t1:
            return rel + (t_src - t0) / speed
        rel += (t1 - t0) / speed
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="out/video/raw/phone_1.mp4")
    ap.add_argument("--only")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    man_path = OUT / "manifest.json"
    manifest = json.loads(man_path.read_text()) if man_path.exists() else {}
    for key, seg in SEGMENTS.items():
        if args.only and key != args.only:
            continue
        manifest[key] = cut(bt709(Path(args.src)), key, seg)
        print(f"{key:12s} {manifest[key]['dur']:6.1f} s  calls={len(manifest[key]['calls'])}")
    man_path.write_text(json.dumps(manifest, indent=1))
    print(f"total {sum(m['dur'] for m in manifest.values()):.0f} s of phone footage")


if __name__ == "__main__":
    main()
