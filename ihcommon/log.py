"""Structured JSON logs. Never log chat IDs or names; hash identifiers first."""

import hashlib
import json
import logging
import sys
import time

_logger = logging.getLogger("invisible-heat")
if not _logger.handlers:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(h)
    _logger.setLevel(logging.INFO)
    _logger.propagate = False


def short_hash(value: str) -> str:
    """Non-reversible short id for logs (not used as a security control)."""
    return hashlib.sha256(str(value).encode()).hexdigest()[:12]


def log(event: str, **fields) -> None:
    _logger.info(json.dumps({"ts": round(time.time(), 3), "event": event, **fields},
                            default=str))


def metric(name: str, value: float = 1, **dims) -> None:
    """CloudWatch Embedded Metric Format: a log line that becomes a metric."""
    print(json.dumps({
        "_aws": {"Timestamp": int(time.time() * 1000), "CloudWatchMetrics": [{
            "Namespace": "InvisibleHeat", "Dimensions": [list(dims)] if dims else [[]],
            "Metrics": [{"Name": name, "Unit": "Count"}]}]},
        name: value, **dims}))
