#!/usr/bin/env bash
# Record the WhatsApp + Hindi call scene from an Android phone over USB (scrcpy), for build_video.py.
#   scripts/video/record_phone.sh            # media audio (voice notes), stops after 40 s or Ctrl+C
#   scripts/video/record_phone.sh mic        # microphone audio: put the call on speaker to capture it
# Then: uv run python scripts/video/build_video.py   (picks up out/video/phone.mp4)
#
# Shot list (about 25 s): open the Pehra chat -> send "hi" -> tap "Mere aur parivar ke liye" ->
# today's plan arrives -> send "paani" + share location -> nearest water -> play the voice note ->
# send "/test_call" (or a family call) -> answer the Hindi call on speaker.
set -euo pipefail
cd "$(dirname "$0")/../.."
mkdir -p out/video
src="${1:-output}"
adb get-state >/dev/null 2>&1 || { echo "No phone found: enable USB debugging and run 'adb devices'"; exit 1; }
exec scrcpy --record=out/video/phone.mp4 --max-size=1920 --video-bit-rate=10M --max-fps=30 \
  --audio-source="$src" --time-limit=40 --stay-awake --show-touches
