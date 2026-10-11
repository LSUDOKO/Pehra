// Pehra brand tokens: the website's palette, one saffron accent, Inter + Noto Sans Devanagari.
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as loadDevanagari } from "@remotion/google-fonts/NotoSansDevanagari";

const inter = loadInter("normal", { weights: ["400", "500", "600", "700", "800"], subsets: ["latin"] });
const deva = loadDevanagari("normal", { weights: ["600", "700"], subsets: ["devanagari"] });

export const FONT = inter.fontFamily;
export const FONT_DEVA = deva.fontFamily;
export const fontsReady = Promise.all([inter.waitUntilDone(), deva.waitUntilDone()]);

export const C = {
  paper: "#f5f1e8",
  surface: "#fffdf8",
  line: "#ded8cb",
  ink: "#192839",
  navy: "#172b3d",
  muted: "#64717a",
  saffron: "#d88b28",
  green: "#356f58",
  red: "#a7453c",
  wa: "#25d366",
} as const;

// Risk levels from heatcore (kam → khatarnak): used only where the product itself shows them.
export const LEVELS = ["#2FB344", "#FFC20E", "#FF8A1F", "#E8282B", "#A266B0"] as const;

export const W = 1920;
export const H = 1080;
export const FPS = 30;
export const MARGIN = 120; // nothing sits in the corners: content lives inside this gutter
