from __future__ import annotations

from datetime import datetime, timezone

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .models import FetchedDocument

USER_AGENT = "OETI/0.2 (+One Health Emerging Threat Intelligence; research prototype)"


@retry(
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.TransportError)),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    stop=stop_after_attempt(3),
    reraise=True,
)
def fetch_document(url: str, timeout_seconds: float = 30.0) -> FetchedDocument:
    with httpx.Client(
        follow_redirects=True,
        timeout=timeout_seconds,
        headers={"User-Agent": USER_AGENT, "Accept-Language": "es-AR,es;q=0.9,en;q=0.6"},
    ) as client:
        response = client.get(url)
        response.raise_for_status()
        return FetchedDocument(
            url=str(response.url),
            status_code=response.status_code,
            mime_type=response.headers.get("content-type"),
            body=response.content,
            retrieved_at=datetime.now(timezone.utc),
            headers={
                key: value
                for key, value in response.headers.items()
                if key.lower() in {"etag", "last-modified", "content-language", "content-type"}
            },
        )
