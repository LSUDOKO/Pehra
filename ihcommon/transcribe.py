"""Amazon Transcribe (hi-IN) for supervisor voice notes. Telegram voice is OGG/Opus."""

import json
import time
import uuid

import boto3

from ihcommon import config

POLL_S = 2
MAX_WAIT_S = 90


def transcribe_ogg(audio: bytes, bucket: str | None = None) -> dict:
    """Returns {'text', 'confidence'}; confidence is the mean word confidence (0-1)."""
    bucket = bucket or config.MEDIA_BUCKET
    job = f"ih-{uuid.uuid4().hex[:16]}"
    s3 = boto3.client("s3", region_name=config.REGION)
    key = f"incoming/{job}.ogg"
    s3.put_object(Bucket=bucket, Key=key, Body=audio, ContentType="audio/ogg")
    tr = boto3.client("transcribe", region_name=config.REGION)
    tr.start_transcription_job(TranscriptionJobName=job, LanguageCode="hi-IN", MediaFormat="ogg",
                               Media={"MediaFileUri": f"s3://{bucket}/{key}"},
                               OutputBucketName=bucket, OutputKey=f"transcripts/{job}.json")
    try:
        deadline = time.time() + MAX_WAIT_S
        while time.time() < deadline:
            st = tr.get_transcription_job(TranscriptionJobName=job)["TranscriptionJob"]
            if st["TranscriptionJobStatus"] in ("COMPLETED", "FAILED"):
                break
            time.sleep(POLL_S)
        if st["TranscriptionJobStatus"] != "COMPLETED":
            return {"text": "", "confidence": 0.0}
        doc = json.loads(s3.get_object(Bucket=bucket, Key=f"transcripts/{job}.json")["Body"].read())
        return parse_result(doc)
    finally:
        s3.delete_object(Bucket=bucket, Key=key)  # do not keep supervisor audio


def parse_result(doc: dict) -> dict:
    text = doc["results"]["transcripts"][0]["transcript"] if doc["results"]["transcripts"] else ""
    confs = [float(i["alternatives"][0]["confidence"]) for i in doc["results"].get("items", [])
             if i.get("type") == "pronunciation"]
    return {"text": text, "confidence": round(sum(confs) / len(confs), 3) if confs else 0.0}
