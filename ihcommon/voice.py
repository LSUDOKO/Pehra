"""Amazon Polly Hindi voice notes (OGG/Opus plays natively as a Telegram voice note)."""

import boto3

from ihcommon import config

VOICE_ID = "Kajal"          # neural, bilingual en-IN / hi-IN
LANGUAGE = "hi-IN"


def synthesize(text: str) -> bytes:
    polly = boto3.client("polly", region_name=config.REGION)
    r = polly.synthesize_speech(Text=text, VoiceId=VOICE_ID, LanguageCode=LANGUAGE,
                                Engine="neural", OutputFormat="ogg_opus")
    return r["AudioStream"].read()


def store(audio: bytes, key: str, bucket: str | None = None) -> str:
    boto3.client("s3", region_name=config.REGION).put_object(
        Bucket=bucket or config.MEDIA_BUCKET, Key=key, Body=audio, ContentType="audio/ogg")
    return key
