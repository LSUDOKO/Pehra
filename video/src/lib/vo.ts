// Narration manifest (from scripts/video/vo.py) and subtitle chunks cut from the word marks.
export type Word = { t: number; w: string; s: number; e: number };
export type Track = { file: string; dur: number; text: string; words: Word[] };
export type Manifest = Record<string, Track>;

export type Chunk = { from: number; to: number; text: string };

const enc = new TextEncoder();
const dec = new TextDecoder();

/** Break the narration into readable lines at sentence ends, long commas, or ~56 characters. */
export function chunks(track: Track): Chunk[] {
  const raw = enc.encode(track.text);
  const out: Chunk[] = [];
  let first: Word | null = null;
  track.words.forEach((w, i) => {
    if (!first) first = w;
    const next = track.words[i + 1];
    const nextStart = next ? next.s : raw.length;
    const tail = dec.decode(raw.slice(w.e, nextStart)).trim();
    const seg = dec.decode(raw.slice(first.s, w.e)) + tail;
    const rest = dec.decode(raw.slice(w.e));
    const toEnd = Math.min(...[". ", "? ", "! "].map((p) => rest.indexOf(p)).filter((x) => x >= 0), rest.length);
    const last = i === track.words.length - 1;
    const sentenceEnd = [".", "?", "!"].includes(tail[0] ?? "");
    const longEnough = seg.length > 56 && toEnd > 16;
    if (last || sentenceEnd || (tail[0] === "," && seg.length > 30) || longEnough || seg.length > 72) {
      out.push({ from: first.t, to: next ? next.t : track.dur + 0.3, text: seg.trim().replace(/,$/, "") });
      first = null;
    }
  });
  return out;
}

/** Seconds at which a word (prefix match, nth occurrence) is spoken, or a fallback. */
export function at(track: Track | undefined, word: string, fallback: number, n = 0): number {
  if (!track) return fallback;
  const hits = track.words.filter((x) => x.w.toLowerCase().replace(/[.,!?'"]/g, "").startsWith(word.toLowerCase()));
  return hits.length > n ? hits[n].t : fallback;
}
