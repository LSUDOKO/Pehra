// Record the live 3D twin page as video (CDP screencast), for the Remotion demo.
//   node scripts/video/record_twin.mjs <twin url> out/video/twin.mp4 [seconds]
// Needs: video/node_modules/playwright-core and a Chromium (PLAYWRIGHT chromium cache or CHROME env).
import { chromium } from "../../video/node_modules/playwright-core/index.mjs";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const [url, out, secs = "24"] = process.argv.slice(2);
if (!url || !out) throw new Error("usage: record_twin.mjs <url> <out.mp4> [seconds]");
const exe = process.env.CHROME || fs.readdirSync(path.join(os.homedir(), ".cache/ms-playwright"))
  .filter((d) => d.startsWith("chromium-")).sort().map((d) => path.join(os.homedir(), ".cache/ms-playwright", d, "chrome-linux64/chrome"))
  .filter(fs.existsSync).pop();
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "twinrec-"));
const browser = await chromium.launch({ executablePath: exe, args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
await page.goto(url, { waitUntil: "networkidle", timeout: 60000 });
await page.waitForTimeout(3000);
const cdp = await page.context().newCDPSession(page);
const frames = [];
cdp.on("Page.screencastFrame", async (ev) => {
  frames.push({ t: ev.metadata.timestamp, data: ev.data });
  await cdp.send("Page.screencastFrameAck", { sessionId: ev.sessionId }).catch(() => {});
});
await cdp.send("Page.startScreencast", { format: "jpeg", quality: 88, maxWidth: 1920, maxHeight: 1080, everyNthFrame: 1 });
const total = Number(secs) * 1000;
await page.waitForTimeout(total * 0.3);
await page.mouse.move(1150, 640);
await page.mouse.down();
for (let i = 0; i < 80; i++) { await page.mouse.move(1150 + i * 3, 640 - i * 0.5); await page.waitForTimeout(40); }
await page.mouse.up();
await page.waitForTimeout(total * 0.55);
await cdp.send("Page.stopScreencast");
await browser.close();
let list = "";
frames.forEach((f, i) => {
  const n = path.join(tmp, `f_${String(i).padStart(5, "0")}.jpg`);
  fs.writeFileSync(n, Buffer.from(f.data, "base64"));
  const d = i + 1 < frames.length ? frames[i + 1].t - f.t : 0.04;
  list += `file '${n}'\nduration ${Math.max(0.01, d).toFixed(4)}\n`;
});
fs.writeFileSync(path.join(tmp, "list.txt"), list);
execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", path.join(tmp, "list.txt"),
  "-vf", "fps=30,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:-1:-1,format=yuv420p",
  "-c:v", "libx264", "-preset", "medium", "-crf", "18", out]);
fs.rmSync(tmp, { recursive: true, force: true });
console.log(`${out}: ${frames.length} frames, ${(frames.at(-1).t - frames[0].t).toFixed(1)} s`);
