from __future__ import annotations

import json
import re
from urllib import error, request


def extract_json(text: str) -> dict:
    cleaned = str(text or "").strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE | re.DOTALL).strip()

    try:
        payload = json.loads(cleaned)
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        payload = json.loads(cleaned[start : end + 1])
        if isinstance(payload, dict):
            return payload
    raise ValueError("model_did_not_return_json")


def message_content(payload: dict) -> str:
    choices = payload.get("choices") or []
    if not choices:
        raise ValueError("no_choices_returned")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, list):
        chunks = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                chunks.append(str(item.get("text") or ""))
        return "".join(chunks).strip()
    return str(content or "").strip()


def request_chat_json(
    settings: dict,
    messages: list[dict],
    *,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int = 1200,
) -> dict:
    body = {
        "model": model or settings["model"],
        "messages": messages,
        "temperature": settings["temperature"] if temperature is None else temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }

    req = request.Request(
        settings["endpoint"],
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings['api_key']}",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=settings["timeout_seconds"]) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"AI provider HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"AI provider unavailable: {exc.reason}") from exc

    return extract_json(message_content(payload))
