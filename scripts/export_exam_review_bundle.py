from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
HANDOFF_DIR = ROOT_DIR / "handoff" / "review"
QUESTIONS_PATH = DATA_DIR / "questions.json"
ANSWER_KEY_PATH = DATA_DIR / "answer_key.json"
OUTPUT_PATH = HANDOFF_DIR / "tem8_exams_in_use_review.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def merge_answers(dataset: dict, answer_key: dict) -> dict:
    merged = deepcopy(dataset)
    total_answered = 0

    for bucket_name in ("years", "library"):
        for entry in merged.get(bucket_name, []):
            for question in entry.get("questions", []):
                answer_entry = answer_key.get(question["id"], {})
                question["correct_option"] = answer_entry.get("correct_option")
                question["display_answer"] = answer_entry.get("display_answer", "")
                question["accepted_answers"] = answer_entry.get("accepted_answers", [])
                question["explanation"] = answer_entry.get("explanation", "")
                if question["correct_option"] or question["display_answer"] or question["accepted_answers"]:
                    total_answered += 1

    merged["meta"] = {
        "generated_at": now_iso(),
        "purpose": "Review bundle for all TEM-8 past exam data currently used by the website.",
        "source_questions": str(QUESTIONS_PATH.relative_to(ROOT_DIR)),
        "source_answer_key": str(ANSWER_KEY_PATH.relative_to(ROOT_DIR)),
        "included_buckets": ["years", "library"],
        "excluded_buckets": ["exercise_sets"],
        "years_included": [entry["year"] for entry in merged.get("years", [])],
        "library_years_included": sorted({entry["year"] for entry in merged.get("library", [])}),
        "year_question_count": sum(entry.get("question_count", 0) for entry in merged.get("years", [])),
        "library_question_count": sum(entry.get("question_count", 0) for entry in merged.get("library", [])),
        "answered_question_count": total_answered,
        "library_sections": [
            {
                "year": entry["year"],
                "section": entry["section"],
                "question_count": entry["question_count"],
            }
            for entry in merged.get("library", [])
        ],
    }
    merged.pop("exercise_sets", None)
    return merged


def main() -> None:
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    dataset = load_json(QUESTIONS_PATH)
    answer_key = load_json(ANSWER_KEY_PATH)
    review_bundle = merge_answers(dataset, answer_key)
    OUTPUT_PATH.write_text(
        json.dumps(review_bundle, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[OK] wrote review bundle: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
