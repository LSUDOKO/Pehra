#!/usr/bin/env bash
# Record the WhatsApp + Hindi call scene from an Android phone over USB (scrcpy), for build_video.py.
#   scripts/video/record_phone.sh            # media audio (voice notes); stop with Ctrl+C
#   scripts/video/record_phone.sh mic        # microphone audio: put the call on speaker to capture it
# Then set the chapter times in scripts/video/phone_cut.py (SEGMENTS), run it, and build_video.py.
#
# Shot list (every feature, any length): open the Pehra chat -> send "hi" -> tap "Mere aur parivar ke liye" ->
# today's plan arrives -> send "paani" + share location -> nearest water -> play the voice note ->
# send "/test_call" (or a family call) -> answer the Hindi call on speaker.
set -euo pipefail
cd "$(dirname "$0")/../.."
mkdir -p out/video/raw
src="${1:-output}"
adb get-state >/dev/null 2>&1 || { echo "No phone found: enable USB debugging and run 'adb devices'"; exit 1; }
exec scrcpy --record=out/video/raw/phone_1.mp4 --max-size=1600 --video-bit-rate=6M --max-fps=30 \
  --audio-source="$src" --stay-awake --show-touches
