from __future__ import annotations

import json
import re
from typing import Any

from app.llm_json import request_chat_json

DEFAULT_RUBRIC_ID = "tem8_essay_general_30"
WORD_TARGET_RE = re.compile(r"(\d{2,4})\s*W[o\u00f6]rter", re.IGNORECASE)
LIST_POINT_RE = re.compile(r"^\s*(?:[a-z]\)|\d+[.)])\s*(.+?)\s*$", re.IGNORECASE)
LINEBREAK_RE = re.compile(r"\r\n?|\n")

ANALYSIS_SYSTEM_PROMPT = """
You are a German TEM-8 essay analysis engine.
Analyze the student's essay only. Do not assign final scores.
Return JSON only. No markdown.
All teacher-facing feedback must be concise Simplified Chinese.

Required top-level keys:
- task_type = "essay"
- analysis_stage = "analysis_only"
- input_summary
- answer_analysis
- language_analysis

input_summary should include:
- word_count_estimate
- length_status
- structure_hint

answer_analysis should include:
- task_completion
- strengths
- gaps
- overall_assessment

task_completion should preferably include:
- covered_points
- partially_covered_points
- missed_points
- comment

language_analysis should include:
- grammar
- vocabulary
- cohesion
- sentence_variety
- comprehensibility
- overall_assessment
""".strip()

SCORING_SYSTEM_PROMPT = """
You are a German TEM-8 essay scoring engine.
Use the prompt profile, rubric, student essay, and prior analysis to assign the final score.
Return JSON only. No markdown.
All teacher-facing feedback must be concise Simplified Chinese.

Required top-level keys:
- task_type = "essay"
- evaluation_version
- input_summary
- answer_analysis
- language_analysis
- scores
- band_judgement
- feedback
- polishing_hooks

scores must include:
- aeussere_form
- sprachliche_form
- inhalt
- total

Each score block must include:
- score
- max_score
- rationale

The total score must equal the sum of aeussere_form, sprachliche_form, and inhalt.
Keep the scoring aligned with the rubric max scores exactly.
""".strip()


def _ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _ensure_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if value is None:
        return {}
    return {"summary": value}


def _coerce_number(value: Any, default: float = 0) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _coerce_score_block(value: Any, *, max_score: float, rationale: str = "") -> dict[str, Any]:
    if isinstance(value, dict):
        return {
            "score": _coerce_number(value.get("score", 0)),
            "max_score": _coerce_number(value.get("max_score", max_score)),
            "rationale": str(value.get("rationale") or rationale).strip(),
        }
    return {
        "score": _coerce_number(value, 0),
        "max_score": _coerce_number(max_score),
        "rationale": rationale,
    }


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        preferred = value.get("comment") or value.get("summary") or value.get("detail") or value.get("note")
        if preferred:
            return str(preferred).strip()
        return "; ".join(f"{key}: {val}" for key, val in value.items() if val not in (None, "", [], {}))
    if isinstance(value, list):
        return "; ".join(part for part in (_text(item) for item in value) if part)
    return str(value).strip()


def _clean_text_list(value: Any, *, limit: int = 6) -> list[str]:
    items: list[str] = []
    for item in _ensure_list(value):
        text = _text(item)
        if text:
            items.append(text)
        if len(items) >= limit:
            break
    return items


def _clean_title(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip(" -:\t"))


def _first_non_empty_line(text: str) -> str:
    for line in LINEBREAK_RE.split(str(text or "")):
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _question_title(question: dict, source_context: dict | None) -> str:
    for value in (
        question.get("stem"),
        _first_non_empty_line(question.get("prompt_text") or ""),
        source_context.get("title") if source_context else "",
    ):
        title = _clean_title(str(value or ""))
        if title:
            return title
    return "Writing Task"


def _target_word_count(question: dict) -> int:
    text = "\n".join(str(part or "") for part in (question.get("prompt_text"), question.get("stem")))
    match = WORD_TARGET_RE.search(text)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass
    return 250


def _extract_required_points(question: dict) -> list[str]:
    subprompts = [str(item).strip() for item in question.get("subprompts") or [] if str(item).strip()]
    if subprompts:
        return subprompts

    points: list[str] = []
    prompt_text = str(question.get("prompt_text") or "")
    for raw_line in LINEBREAK_RE.split(prompt_text):
        line = raw_line.strip()
        if not line:
            continue
        match = LIST_POINT_RE.match(line)
        if match:
            point = match.group(1).strip()
            if point:
                points.append(point)
                continue
        if line[-1:] in {"?", "!"} and len(line) > 20 and not line.lower().startswith("aufgabe:"):
            points.append(line)

    deduped: list[str] = []
    seen = set()
    for point in points:
        normalized = point.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(point)
    return deduped[:5]


def _estimate_word_count(text: str) -> int:
    return len(re.findall(r"\b[\w\u00c0-\u024f'-]+\b", str(text or ""), flags=re.UNICODE))


def _length_status(word_count: int, soft_min: int, soft_max: int) -> str:
    if word_count <= 0:
        return "missing"
    if word_count < soft_min:
        return "underlength"
    if word_count > soft_max:
        return "overlength"
    return "on_target"


def build_essay_prompt_data(question: dict, source_context: dict | None) -> dict[str, Any]:
    target_word_count = _target_word_count(question)
    required_points = _extract_required_points(question)
    return {
        "prompt_id": question.get("id") or "writing-task",
        "task_type": "essay",
        "title": _question_title(question, source_context),
        "target_word_count": target_word_count,
        "word_count": {
            "soft_min": max(180, target_word_count - 20),
            "soft_max": target_word_count + 20,
            "notes": [
                f"Around {target_word_count} words are expected.",
                "A clearly underlength or overlength essay should reduce form score.",
                "A very short essay may also reduce content score.",
            ],
        },
        "instructions": str((source_context or {}).get("instruction") or "").strip()
        or "Write a connected essay, address all task points, and justify your opinion.",
        "required_points": required_points,
        "recommended_rubric_id": DEFAULT_RUBRIC_ID,
    }


def build_essay_prompt_profile(prompt_data: dict[str, Any]) -> dict[str, Any]:
    required_points = prompt_data.get("required_points") or []
    teacher_focus = [
        f"Check whether the word count is close to {prompt_data['target_word_count']}.",
        "Check whether the essay has a recognisable introduction-body-conclusion structure.",
        "Check whether arguments are explained rather than listed mechanically.",
    ]
    if required_points:
        teacher_focus.append(f"Check whether all {len(required_points)} task points are covered.")
    return {
        "prompt_id": prompt_data["prompt_id"],
        "display_name": f"TEM8 Writing {prompt_data['title']}",
        "analysis_hint": "Focus on task coverage, approximate word count, and basic essay structure.",
        "scoring_hint": "Length matters strongly for aeussere_form. Missing task points should reduce inhalt.",
        "calibration_note": "Do not over-reward short checklist-style answers that touch points without development.",
        "teacher_focus": teacher_focus,
    }


def build_essay_rubric(prompt_data: dict[str, Any], source_context: dict | None) -> dict[str, Any]:
    required_points = prompt_data.get("required_points") or []
    task_checklist = {
        f"point_{index}": {
            "label": point,
            "required": True,
            "examples": [],
        }
        for index, point in enumerate(required_points, start=1)
    }
    return {
        "rubric_id": DEFAULT_RUBRIC_ID,
        "exam_type": "TEM8",
        "year": (source_context or {}).get("year"),
        "task_type": "essay",
        "prompt_title": prompt_data["title"],
        "target_word_count": prompt_data["target_word_count"],
        "word_count": prompt_data["word_count"],
        "dimensions": {
            "aeussere_form": {
                "max_score": 2,
                "criteria": ["readability", "basic_structure", "reasonable_length", "formal_completeness"],
                "bands": [
                    {"score": 2.0, "descriptor": "Structure complete, readable, appropriate length, all required parts present."},
                    {"score": 1.0, "descriptor": "Minor problems in structure or length."},
                    {"score": 0.0, "descriptor": "Major formal problems or clearly inappropriate length/structure."},
                ],
            },
            "sprachliche_form": {
                "max_score": 15,
                "criteria": [
                    "grammar_accuracy",
                    "spelling_accuracy",
                    "lexical_range",
                    "cohesion",
                    "sentence_variety",
                    "comprehensibility",
                ],
                "bands": [
                    {"score": 15.0, "descriptor": "Fluent and appropriate expression, varied sentence structures, few errors."},
                    {"score": 12.0, "descriptor": "Generally appropriate, some errors partly affect comprehension."},
                    {"score": 9.0, "descriptor": "Simple expression, limited linkage, more frequent errors."},
                    {"score": 6.0, "descriptor": "Many errors and awkward expression; understanding becomes difficult."},
                    {"score": 3.0, "descriptor": "Severely flawed language; large parts are hard to understand."},
                    {"score": 0.0, "descriptor": "Not understandable or not a valid response."},
                ],
            },
            "inhalt": {
                "max_score": 13,
                "criteria": ["task_completion", "relevance", "argument_development", "logical_organization"],
                "bands": [
                    {"score": 13.0, "descriptor": "All task points fully addressed; arguments developed and logically organized."},
                    {"score": 11.0, "descriptor": "All task points covered overall, but one part is less developed."},
                    {"score": 9.0, "descriptor": "Noticeable content gaps or one task point insufficiently addressed."},
                    {"score": 6.0, "descriptor": "Significant omissions or weak organization."},
                    {"score": 3.0, "descriptor": "Most requirements not met."},
                    {"score": 0.0, "descriptor": "Off-topic or almost no valid content."},
                ],
            },
        },
        "task_checklist": task_checklist,
    }


def _analysis_messages(
    prompt_data: dict[str, Any],
    profile_data: dict[str, Any],
    rubric_data: dict[str, Any],
    response_text: str,
) -> list[dict[str, str]]:
    user_content = (
        "Mode: analysis_only\n\n"
        f"Prompt JSON:\n{json.dumps(prompt_data, ensure_ascii=False, indent=2)}\n\n"
        f"Prompt profile JSON:\n{json.dumps(profile_data, ensure_ascii=False, indent=2)}\n\n"
        f"Rubric JSON:\n{json.dumps(rubric_data, ensure_ascii=False, indent=2)}\n\n"
        f"Student essay:\n{response_text.strip()}\n"
    )
    return [{"role": "system", "content": ANALYSIS_SYSTEM_PROMPT}, {"role": "user", "content": user_content}]


def _scoring_messages(
    prompt_data: dict[str, Any],
    profile_data: dict[str, Any],
    rubric_data: dict[str, Any],
    response_text: str,
    analysis_json: dict[str, Any],
) -> list[dict[str, str]]:
    user_content = (
        "Mode: full\n\n"
        f"Prompt JSON:\n{json.dumps(prompt_data, ensure_ascii=False, indent=2)}\n\n"
        f"Prompt profile JSON:\n{json.dumps(profile_data, ensure_ascii=False, indent=2)}\n\n"
        f"Rubric JSON:\n{json.dumps(rubric_data, ensure_ascii=False, indent=2)}\n\n"
        f"Student essay:\n{response_text.strip()}\n\n"
        f"Analysis JSON:\n{json.dumps(analysis_json, ensure_ascii=False, indent=2)}\n"
    )
    return [{"role": "system", "content": SCORING_SYSTEM_PROMPT}, {"role": "user", "content": user_content}]


def normalize_essay_analysis(raw: dict[str, Any], *, prompt_data: dict[str, Any], response_text: str) -> dict[str, Any]:
    answer_analysis = _ensure_dict(raw.get("answer_analysis"))
    language_analysis = _ensure_dict(raw.get("language_analysis"))
    task_completion = _ensure_dict(answer_analysis.get("task_completion") or answer_analysis.get("task_checklist_alignment"))
    soft_min = int(prompt_data["word_count"]["soft_min"])
    soft_max = int(prompt_data["word_count"]["soft_max"])
    word_count_estimate = _estimate_word_count(response_text)

    return {
        "task_type": "essay",
        "analysis_stage": "analysis_only",
        "prompt_id": prompt_data["prompt_id"],
        "rubric_id": prompt_data["recommended_rubric_id"],
        "input_summary": {
            "word_count_estimate": word_count_estimate,
            "length_status": _length_status(word_count_estimate, soft_min, soft_max),
            "structure_hint": str(_text(_ensure_dict(raw.get("input_summary")).get("structure_hint")) or "").strip(),
        },
        "answer_analysis": {
            "task_completion": {
                "covered_points": _clean_text_list(task_completion.get("covered_points")),
                "partially_covered_points": _clean_text_list(task_completion.get("partially_covered_points")),
                "missed_points": _clean_text_list(task_completion.get("missed_points")),
                "comment": _text(task_completion.get("comment") or task_completion.get("summary")),
            },
            "strengths": _clean_text_list(answer_analysis.get("strengths") or answer_analysis.get("content_strengths")),
            "gaps": _clean_text_list(answer_analysis.get("gaps") or answer_analysis.get("content_gaps") or answer_analysis.get("content_weaknesses")),
            "overall_assessment": _text(answer_analysis.get("overall_assessment") or answer_analysis.get("overall_content_assessment")),
        },
        "language_analysis": {
            "grammar": _text(language_analysis.get("grammar") or language_analysis.get("grammar_accuracy")),
            "vocabulary": _text(language_analysis.get("vocabulary") or language_analysis.get("lexical_range")),
            "cohesion": _text(language_analysis.get("cohesion")),
            "sentence_variety": _text(language_analysis.get("sentence_variety")),
            "comprehensibility": _text(language_analysis.get("comprehensibility")),
            "overall_assessment": _text(language_analysis.get("overall_assessment") or language_analysis.get("overall_language_assessment")),
        },
    }


def normalize_essay_score(
    raw: dict[str, Any],
    *,
    prompt_data: dict[str, Any],
    rubric_data: dict[str, Any],
    analysis_json: dict[str, Any],
    model: str,
    provider: str,
) -> dict[str, Any]:
    scores = _ensure_dict(raw.get("scores"))
    band = _ensure_dict(raw.get("band_judgement"))
    feedback = _ensure_dict(raw.get("feedback"))
    polishing_hooks = _ensure_dict(raw.get("polishing_hooks"))

    aeussere_form = _coerce_score_block(
        scores.get("aeussere_form"),
        max_score=rubric_data["dimensions"]["aeussere_form"]["max_score"],
        rationale=_text(_ensure_dict(band).get("aeussere_form")),
    )
    sprachliche_form = _coerce_score_block(
        scores.get("sprachliche_form"),
        max_score=rubric_data["dimensions"]["sprachliche_form"]["max_score"],
        rationale=_text(_ensure_dict(band).get("sprachliche_form")),
    )
    inhalt = _coerce_score_block(
        scores.get("inhalt"),
        max_score=rubric_data["dimensions"]["inhalt"]["max_score"],
        rationale=_text(_ensure_dict(band).get("inhalt")),
    )
    total_score = aeussere_form["score"] + sprachliche_form["score"] + inhalt["score"]

    feedback_overall = _text(feedback.get("overall") or feedback.get("summary"))
    next_steps = _clean_text_list(feedback.get("next_steps") or feedback.get("recommendations"))
    focus_areas = _clean_text_list(polishing_hooks.get("focus_areas"))
    if not next_steps:
        next_steps = focus_areas
    if not feedback_overall:
        feedback_overall = (
            _text(analysis_json["answer_analysis"].get("overall_assessment"))
            or _text(analysis_json["language_analysis"].get("overall_assessment"))
            or "AI completed the essay review."
        )

    return {
        "task_type": "essay",
        "evaluation_version": str(raw.get("evaluation_version") or "1.0"),
        "prompt_id": prompt_data["prompt_id"],
        "rubric_id": rubric_data["rubric_id"],
        "meta": {"model_provider": provider, "model_name": model},
        "input_summary": analysis_json["input_summary"],
        "answer_analysis": analysis_json["answer_analysis"],
        "language_analysis": analysis_json["language_analysis"],
        "scores": {
            "aeussere_form": aeussere_form,
            "sprachliche_form": sprachliche_form,
            "inhalt": inhalt,
            "total": {
                "score": total_score,
                "max_score": (
                    rubric_data["dimensions"]["aeussere_form"]["max_score"]
                    + rubric_data["dimensions"]["sprachliche_form"]["max_score"]
                    + rubric_data["dimensions"]["inhalt"]["max_score"]
                ),
                "rationale": _text(_ensure_dict(scores.get("total")).get("rationale")),
            },
        },
        "band_judgement": {
            "band": _text(band.get("band")),
            "summary": _text(band.get("summary") or band.get("overall")),
            "dimension_notes": {
                "aeussere_form": _text(band.get("aeussere_form")),
                "sprachliche_form": _text(band.get("sprachliche_form")),
                "inhalt": _text(band.get("inhalt")),
            },
        },
        "feedback": {"overall": feedback_overall, "next_steps": next_steps},
        "polishing_hooks": {
            "can_expand_to_polishing": bool(polishing_hooks.get("can_expand_to_polishing", True)),
            "focus_areas": focus_areas,
        },
    }


def _append_issue(issues: list[dict[str, str]], title: str, detail: str, *, limit: int = 6) -> None:
    cleaned_title = _text(title) or "Issue"
    cleaned_detail = _text(detail)
    if not cleaned_detail or len(issues) >= limit:
        return
    if any(item["detail"] == cleaned_detail for item in issues):
        return
    issues.append({"title": cleaned_title, "detail": cleaned_detail})


def to_review_payload(evaluation: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    task_completion = evaluation["answer_analysis"].get("task_completion") or {}
    for point in task_completion.get("missed_points") or []:
        _append_issue(issues, "Task coverage", point)
    for gap in evaluation["answer_analysis"].get("gaps") or []:
        _append_issue(issues, "Content", gap)
    for label, key in (
        ("Grammar", "grammar"),
        ("Vocabulary", "vocabulary"),
        ("Cohesion", "cohesion"),
        ("Sentence variety", "sentence_variety"),
    ):
        _append_issue(issues, label, evaluation["language_analysis"].get(key))

    suggestions = evaluation["feedback"].get("next_steps") or []
    if not suggestions:
        suggestions = evaluation["polishing_hooks"].get("focus_areas") or []

    return {
        "task_type": "writing",
        "score": int(round(evaluation["scores"]["total"]["score"])),
        "max_score": int(round(evaluation["scores"]["total"]["max_score"])),
        "summary": evaluation["feedback"]["overall"],
        "issues": issues,
        "suggestions": suggestions[:6],
        "revised_answer": "",
        "provider": evaluation["meta"]["model_provider"],
        "model": evaluation["meta"]["model_name"],
        "rubric_breakdown": evaluation["scores"],
        "band_summary": evaluation["band_judgement"].get("summary") or "",
        "analysis": {
            "task_completion": task_completion,
            "strengths": evaluation["answer_analysis"].get("strengths") or [],
            "gaps": evaluation["answer_analysis"].get("gaps") or [],
            "overall_content": evaluation["answer_analysis"].get("overall_assessment") or "",
            "grammar": evaluation["language_analysis"].get("grammar") or "",
            "vocabulary": evaluation["language_analysis"].get("vocabulary") or "",
            "cohesion": evaluation["language_analysis"].get("cohesion") or "",
            "sentence_variety": evaluation["language_analysis"].get("sentence_variety") or "",
            "comprehensibility": evaluation["language_analysis"].get("comprehensibility") or "",
            "overall_language": evaluation["language_analysis"].get("overall_assessment") or "",
        },
    }


def request_essay_review(settings: dict, question: dict, source_context: dict | None, response_text: str) -> dict[str, Any]:
    prompt_data = build_essay_prompt_data(question, source_context)
    profile_data = build_essay_prompt_profile(prompt_data)
    rubric_data = build_essay_rubric(prompt_data, source_context)
    analysis_model = str(settings.get("essay_analysis_model") or settings.get("model") or "").strip()
    scoring_model = str(settings.get("essay_scoring_model") or settings.get("model") or "").strip()

    analysis_raw = request_chat_json(
        settings,
        _analysis_messages(prompt_data, profile_data, rubric_data, response_text),
        model=analysis_model,
        max_tokens=1600,
    )
    analysis_json = normalize_essay_analysis(
        analysis_raw,
        prompt_data=prompt_data,
        response_text=response_text,
    )

    scoring_raw = request_chat_json(
        settings,
        _scoring_messages(prompt_data, profile_data, rubric_data, response_text, analysis_json),
        model=scoring_model,
        max_tokens=1800,
    )
    evaluation = normalize_essay_score(
        scoring_raw,
        prompt_data=prompt_data,
        rubric_data=rubric_data,
        analysis_json=analysis_json,
        model=scoring_model,
        provider=str(settings.get("provider") or ""),
    )
    return to_review_payload(evaluation)
