from __future__ import annotations

import json
import os
import re
from copy import deepcopy
from pathlib import Path

from app.essay_review import request_essay_review
from app.llm_json import request_chat_json

DEFAULT_SETTINGS = {
    "enabled": False,
    "provider": "deepseek",
    "endpoint": "https://api.deepseek.com/chat/completions",
    "model": "deepseek-chat",
    "essay_analysis_model": "",
    "essay_scoring_model": "",
    "api_key": "",
    "timeout_seconds": 120,
    "temperature": 0.3,
}

ENV_MAPPING = {
    "enabled": "TEM8_AI_ENABLED",
    "provider": "TEM8_AI_PROVIDER",
    "endpoint": "TEM8_AI_ENDPOINT",
    "model": "TEM8_AI_MODEL",
    "essay_analysis_model": "TEM8_AI_ESSAY_ANALYSIS_MODEL",
    "essay_scoring_model": "TEM8_AI_ESSAY_SCORING_MODEL",
    "api_key": "TEM8_AI_API_KEY",
    "timeout_seconds": "TEM8_AI_TIMEOUT_SECONDS",
    "temperature": "TEM8_AI_TEMPERATURE",
}

POINTS_PATTERN = re.compile(r"\((\d+)\s*(?:P|Punkte)\)", re.IGNORECASE)


def _coerce_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _coerce_int(value, fallback: int) -> int:
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return fallback


def _coerce_float(value, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def load_ai_settings(path: Path) -> dict:
    settings = deepcopy(DEFAULT_SETTINGS)
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            settings.update(payload)

    for key, env_name in ENV_MAPPING.items():
        env_value = os.getenv(env_name)
        if env_value is None or env_value == "":
            continue
        settings[key] = env_value

    settings["enabled"] = _coerce_bool(settings.get("enabled"))
    settings["timeout_seconds"] = _coerce_int(settings.get("timeout_seconds"), DEFAULT_SETTINGS["timeout_seconds"])
    settings["temperature"] = _coerce_float(settings.get("temperature"), DEFAULT_SETTINGS["temperature"])
    settings["provider"] = str(settings.get("provider") or DEFAULT_SETTINGS["provider"]).strip() or DEFAULT_SETTINGS["provider"]
    settings["endpoint"] = str(settings.get("endpoint") or DEFAULT_SETTINGS["endpoint"]).strip() or DEFAULT_SETTINGS["endpoint"]
    settings["model"] = str(settings.get("model") or DEFAULT_SETTINGS["model"]).strip() or DEFAULT_SETTINGS["model"]
    settings["essay_analysis_model"] = str(settings.get("essay_analysis_model") or "").strip()
    settings["essay_scoring_model"] = str(settings.get("essay_scoring_model") or "").strip()
    settings["api_key"] = str(settings.get("api_key") or "").strip()
    settings["configured"] = bool(settings["enabled"] and settings["endpoint"] and settings["model"] and settings["api_key"])
    return settings


def public_ai_settings(settings: dict) -> dict:
    return {
        "enabled": bool(settings.get("enabled")),
        "configured": bool(settings.get("configured")),
        "provider": settings.get("provider") or DEFAULT_SETTINGS["provider"],
        "model": settings.get("model") or DEFAULT_SETTINGS["model"],
    }


def _task_label(question: dict, source_context: dict | None) -> str:
    category = str((source_context or {}).get("category") or "").strip().lower()
    if category in {"translation", "writing"}:
        return category
    if question.get("question_type") == "prompt":
        return "open-response"
    return "general"


def _max_score(question: dict, source_context: dict | None) -> int:
    for value in (
        question.get("prompt_text"),
        question.get("stem"),
        (source_context or {}).get("instruction"),
        (source_context or {}).get("title"),
    ):
        match = POINTS_PATTERN.search(str(value or ""))
        if match:
            return int(match.group(1))

    task_label = _task_label(question, source_context)
    if task_label == "translation":
        return 25
    if task_label == "writing":
        return 30
    return 100


def _normalize_issues(raw_issues) -> list[dict]:
    issues = []
    for item in raw_issues or []:
        if len(issues) >= 6:
            break
        if isinstance(item, str):
            text = item.strip()
            if text:
                issues.append({"title": "Issue", "detail": text})
            continue
        if isinstance(item, dict):
            title = str(item.get("title") or item.get("type") or "Issue").strip()
            detail = str(item.get("detail") or item.get("description") or "").strip()
            if detail:
                issues.append({"title": title or "Issue", "detail": detail})
    return issues


def _normalize_suggestions(raw_suggestions) -> list[str]:
    suggestions = []
    for item in raw_suggestions or []:
        if len(suggestions) >= 6:
            break
        text = ""
        if isinstance(item, str):
            text = item.strip()
        elif isinstance(item, dict):
            text = str(item.get("text") or item.get("detail") or "").strip()
        if text:
            suggestions.append(text)
    return suggestions


def _review_messages(question: dict, source_context: dict | None, response_text: str, max_score: int) -> list[dict]:
    task_label = _task_label(question, source_context)
    rubric = {
        "translation": "Focus on meaning accuracy, completeness, terminology, fluency, and grammar.",
        "writing": "Focus on task fulfillment, structure, argument quality, vocabulary, and grammar.",
        "open-response": "Focus on whether the response addresses the prompt clearly and correctly.",
        "general": "Focus on clarity, correctness, and relevance.",
    }[task_label]

    prompt_payload = {
        "task_type": task_label,
        "max_score": max_score,
        "question_title": question.get("stem") or "",
        "question_prompt": question.get("prompt_text") or "",
        "subprompts": question.get("subprompts") or [],
        "source_title": (source_context or {}).get("title") or "",
        "source_category": (source_context or {}).get("category") or "",
        "student_response": response_text.strip(),
    }

    return [
        {
            "role": "system",
            "content": (
                "You are a concise German exam reviewer. "
                "Return JSON only with keys: score, summary, issues, suggestions, revised_answer. "
                "issues must be an array of objects with title and detail. "
                "suggestions must be an array of short strings."
            ),
        },
        {
            "role": "user",
            "content": (
                f"{rubric}\n"
                "Keep the tone practical and short. "
                "If the prompt or OCR text is damaged, mention that briefly in summary or issues.\n\n"
                f"{json.dumps(prompt_payload, ensure_ascii=False)}"
            ),
        },
    ]


def request_ai_review(settings: dict, question: dict, source_context: dict | None, response_text: str) -> dict:
    if not settings.get("configured"):
        raise RuntimeError("AI review is not configured.")

    task_label = _task_label(question, source_context)
    if task_label == "writing":
        return request_essay_review(settings, question, source_context, response_text)

    max_score = _max_score(question, source_context)
    raw_review = request_chat_json(
        settings,
        _review_messages(question, source_context, response_text, max_score),
        max_tokens=1200,
    )
    score = raw_review.get("score")
    try:
        score = int(round(float(score)))
    except (TypeError, ValueError):
        score = max_score // 2
    score = max(0, min(max_score, score))

    return {
        "task_type": task_label,
        "score": score,
        "max_score": max_score,
        "summary": str(raw_review.get("summary") or "AI review completed.").strip(),
        "issues": _normalize_issues(raw_review.get("issues")),
        "suggestions": _normalize_suggestions(raw_review.get("suggestions")),
        "revised_answer": str(raw_review.get("revised_answer") or "").strip(),
        "provider": settings["provider"],
        "model": settings["model"],
    }
