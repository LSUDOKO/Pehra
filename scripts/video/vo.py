"""Narration for the Remotion brand video: Amazon Polly (Kajal, neural) per scene, with word marks.

    uv run python scripts/video/vo.py            # writes video/public/vo/<scene>.mp3 + manifest.json
Every number in the script comes from docs/results/ and the live site. Scenes are told in order:
the problem fully first, then Pehra, then the Site Box, then how it runs.
"""

import hashlib
import json
import subprocess
from pathlib import Path

import boto3

OUT = Path("video/public/vo")
VOICE, LANG = "Kajal", "en-IN"

SCRIPT = {
    # ---- act 1: the problem, told fully ----
    "open": "Every summer, India measures heat with a thermometer. But a thermometer cannot feel what a body feels.",
    "humidity": "The body cools itself by sweating. On a humid day, sweat does not dry, and the cooling stops. "
                "So a humid 36 degree day can hurt a worker more than a dry 42 degree day.",
    "wbgt": "Safety scientists measure this with W B G T: one number that combines temperature, humidity, sun and wind. "
            "It is what the US and many armies use to decide when work must stop. India's public heat alerts still use temperature alone.",
    "kharghar": "16 April 2023, Kharghar, near Mumbai. People died of heatstroke at an open-air event. "
                "The maximum temperature that day was 38.8 degrees. Under the official rule, that is not a heatwave. No alert.",
    "kharghar_wbgt": "We replayed that day with weather reanalysis data. W B G T in the sun crossed the safe limit for moderate work "
                     "from ten in the morning to four in the afternoon, peaking at 30.8 degrees at noon. The danger was real. It was just invisible.",
    "audit": "So we checked how often this happens. Twelve cities, five years, 2021 to 2025. "
             "4,372 city-days crossed the W B G T work limit while no heatwave was declared. That is 97 percent of all such days. "
             "2,327 of them fell outside March to June, when heatwave bulletins do not even run. These are published on the Pehra audit page, "
             "with the method and every caveat.",
    "water": "The same years held 90 days of heavy rain and 68 warm nights, when the body cannot recover at night. "
             "Heat and water are one problem.",
    # ---- act 2: Pehra ----
    "intro": "Pehra means guard. It is a heat and water guard that lives on WhatsApp, in Hindi, with no app to install. "
             "It turns the free weather forecast into W B G T, and W B G T into a plan for the day.",
    "story_supervisor": "The first story. Ramesh runs a construction site in Kharghar. On a real phone, he registers the site "
                        "and types his crew in plain Hindi: forty people, ten on heavy work, three new. "
                        "Pehra reads it back, and he confirms.",
    "story_supervisor_plan": "Every evening at seven, he gets tomorrow's plan: when to stop work, how many minutes of rest each hour, "
                             "how much water to stock. It comes as text and as a Hindi voice note. He approves it with one tap, "
                             "and the plan is saved to a tamper-proof record.",
    "story_worker": "The second story. Gurpreet works on that site. He scans the site QR code. No app, no login. "
                    "He logs his rest break. If he feels dizzy, he taps chakkar, and sees fixed first aid. "
                    "At that moment Ramesh gets a WhatsApp alert, and his phone rings with a Hindi call.",
    "story_ask": "Ramesh can also just ask. Can we pour concrete at two tomorrow? Pehra answers from the plan's own numbers: "
                 "no, heavy work is stopped then. The AI explains, but it never does the maths, and it can never loosen a limit.",
    "story_family": "The third story. Meena is expecting, and lives with her small son and her mother-in-law in Mumbai. "
                    "She says hi, answers five button questions about her household, counts only, never names, "
                    "and gets today's plan with stricter limits for the vulnerable. On dangerous days, Dadi gets a Hindi phone call.",
    "story_vendor": "The fourth story. Lakshmi sells fruit on a Delhi street. She types paani, Connaught Place, "
                    "and gets the nearest drinking water, 190 metres away, with a map link. Schools and delivery riders get their own plans too.",
    # ---- act 3: the Site Box ----
    "box_why": "Some sites have no smartphone at all. For them, Pehra is a box.",
    "box_what": "The Pehra Site Box is about 600 rupees of parts around an E S P 32. A humidity sensor reads the air. "
                "A probe inside a matt black globe reads the heat of the sun and the concrete. Together they give the real W B G T on that site, "
                "every ten seconds. Two sonar sensors watch the drinking water tank and the drain.",
    "box_does": "The box does not just measure. It acts. The ring shows the risk colour. A siren rings when it is time to rest. "
               "A relay turns on a mist fan. Another refills the tank. And a red button calls for help.",
    "box_sim": "Here it is running in the Wokwi simulator, with the real firmware. The readings go to AWS IoT Core over a secure certificate. "
               "A rule hands them to a Lambda function, which computes W B G T, applies the plan, and publishes the command back to the box.",
    "box_twin": "Every box gets a live 3D twin on the web. The twin shows what the box sees: the risk, the rest, the tank, the fan, the pump. "
                "When the SOS button is pressed, the twin turns red, the supervisor gets a WhatsApp alert, and a Hindi call.",
    # ---- act 4: how it runs ----
    "arch": "Under the hood, Pehra is one serverless stack on AWS, in Mumbai. The forecast becomes W B G T once per city, "
            "so a million sites cost the same as one. Step Functions waits for the supervisor's approval. "
            "Amazon Bedrock explains the plan, Cedar policy makes sure the AI can never loosen it, Polly speaks Hindi, "
            "and every day's record is locked in S3.",
    "honest": "What Pehra does not claim: it does not save lives, and it is not medical advice. It is designed to reduce exposure, "
              "and every number it sends comes from code, never from the model.",
    "outro": "Pehra. A guard for the heat you cannot see. Built on AWS by Team Mavricks.",
}

# ---- the 6 to 7 minute cut: characters read the real chats ----
SCRIPT.update({
    "v2_open": "India warns its people with a thermometer. But the heat that hurts is the heat you cannot see. This is Pehra.",
    "v2_problem": "Heat and humidity together are measured as W B G T. On 16 April 2023, in Kharghar, people died of heatstroke "
                  "at an open-air event. It was 38.8 degrees, so there was no heatwave alert. But W B G T in the sun reached 30.8, "
                  "far above the safe work limit of 28.2.",
    "v2_audit": "Our audit, live on the Pehra website, found 4,372 such days in twelve cities over five years, with no alert. "
                "2,327 of them fell outside the heatwave season. Every number is shown with its caveats.",
    "v2_intro": "Pehra turns the free forecast into W B G T, and W B G T into a plan, in Hindi, on WhatsApp. No app to install. "
                "Here is how four people use it.",
    "v2_ramesh": "Ramesh runs a construction site in Kharghar. He types his crew in Hindi: forty people, ten on heavy work, three new. "
                 "Pehra reads it back. Then it sends tomorrow's plan: stop work from nine to five, rest every hour around it, "
                 "new workers at twenty percent, and seven big cans of water. The same plan comes as a Hindi voice note. "
                 "He taps Approve, and it is saved to the record.",
    "v2_ask": "He asks: can we pour concrete at two tomorrow? Pehra answers: no, heavy work is stopped in the afternoon. "
              "The AI explains, but every number comes from code.",
    "v2_gurpreet": "Gurpreet works on that site. He scans the site QR code. No app, no login. He logs his rest. "
                   "When he feels dizzy, he taps chakkar, and sees first aid: stop work, go to the shade, drink water slowly. "
                   "At that moment Ramesh gets this alert, and his phone rings in Hindi.",
    "v2_meena": "Meena is expecting, and lives with her son and her mother-in-law in Mumbai. She says hi, and answers five quick "
                "questions. Her plan reads: today is khatarnak. The elderly, children and pregnant women should stay inside "
                "from nine to five. And on a day like this, Dadi gets a phone call in Hindi.",
    "v2_lakshmi": "Lakshmi sells fruit in Delhi. She types: paani, Connaught Place. Pehra replies with drinking water 190 metres "
                  "away, and a water A T M at 220 metres, with map links.",
    "v2_box": "Some sites have no smartphone. For them, Pehra is a six hundred rupee box. A humidity sensor and a black globe "
              "measure the real W B G T on site. Sonar watches the water tank and the drain. It rings a rest siren, runs a "
              "mist fan, refills the tank, and has an SOS button.",
    "v2_sim": "Here is the real firmware running in the Wokwi simulator. A hot day: W B G T 35.7, khatarnak, sixty minutes of "
              "rest every hour, work stopped.",
    "v2_twin": "Readings go to AWS IoT Core, and every box gets a live 3D twin. When a worker presses SOS, the twin turns red, "
               "Ramesh gets a WhatsApp alert, and a Hindi call.",
    "v2_arch": "Under the hood it is one serverless stack on AWS in Mumbai. The forecast becomes W B G T once per city. "
               "Step Functions waits for Approve. Bedrock explains, Cedar makes sure the AI can never loosen a limit, "
               "Polly speaks Hindi, and every record is locked in S3.",
    "v2_proof": "And this is the real account: the deployed stack, the IoT thing and its rule, the Step Functions runs, "
                "the locked records, and the six Hindi calls from today's test.",
    "v2_outro": "Pehra does not claim to save lives. It is designed to reduce exposure. Pehra. A guard for the heat you cannot see.",
})


def synth(key: str, text: str) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha1(f"{VOICE}|{LANG}|{text}".encode()).hexdigest()[:10]
    mp3, marks = OUT / f"{key}.mp3", OUT / f"{key}.json"
    stamp = OUT / f"{key}.{h}.ok"
    if not stamp.exists():
        p = boto3.client("polly", region_name="ap-south-1")
        kw = dict(Text=text, VoiceId=VOICE, Engine="neural", LanguageCode=LANG)
        mp3.write_bytes(p.synthesize_speech(OutputFormat="mp3", SampleRate="24000", **kw)["AudioStream"].read())
        marks.write_bytes(p.synthesize_speech(OutputFormat="json", SpeechMarkTypes=["word"], **kw)["AudioStream"].read())
        for old in OUT.glob(f"{key}.*.ok"):
            old.unlink()
        stamp.touch()
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp3)],
                               capture_output=True, text=True).stdout.strip())
    words = [{"t": j["time"] / 1000, "w": j["value"], "s": j["start"], "e": j["end"]}
             for j in map(json.loads, marks.read_text().splitlines()) if j]
    return {"file": f"vo/{key}.mp3", "dur": round(dur, 3), "text": text, "words": words}


if __name__ == "__main__":
    man = {k: synth(k, t) for k, t in SCRIPT.items()}
    (OUT / "manifest.json").write_text(json.dumps(man, ensure_ascii=False))
    total = sum(m["dur"] for m in man.values())
    for k, m in man.items():
        print(f"{k:24s} {m['dur']:6.1f}")
    print(f"narration total {total / 60:.1f} min")
