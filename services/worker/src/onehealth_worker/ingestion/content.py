from __future__ import annotations

import hashlib
import re


def normalized_text_sha256(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip().encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()
