from __future__ import annotations

import filecmp
import shutil
import sys
from pathlib import Path

APP_NAME = "TEM8Practice"
IS_FROZEN = bool(getattr(sys, "frozen", False))
SOURCE_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", SOURCE_ROOT))


def resolve_runtime_root() -> Path:
    if not IS_FROZEN:
        return SOURCE_ROOT
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    return Path(sys.executable).resolve().parent


RUNTIME_ROOT = resolve_runtime_root()

STATIC_DIR = BUNDLE_ROOT / "app" / "static"
BUNDLE_DATA_DIR = BUNDLE_ROOT / "data"
DATA_DIR = RUNTIME_ROOT / "data"
LOG_DIR = RUNTIME_ROOT / "logs"

QUESTIONS_PATH = DATA_DIR / "questions.json"
ANSWER_KEY_PATH = DATA_DIR / "answer_key.json"
ANSWER_TEMPLATE_PATH = DATA_DIR / "answer_key.template.json"
AI_REVIEW_SETTINGS_PATH = DATA_DIR / "ai_review.json"
AI_REVIEW_TEMPLATE_PATH = DATA_DIR / "ai_review.template.json"
PROGRESS_PATH = DATA_DIR / "user_progress.json"
EVENT_LOG_PATH = LOG_DIR / "events.jsonl"

SEED_DATA_FILES = (
    "questions.json",
    "answer_key.json",
    "answer_key.template.json",
    "ai_review.template.json",
)


def _should_refresh_seed(source_path: Path, target_path: Path) -> bool:
    if not source_path.exists():
        return False
    if source_path == target_path:
        return False
    if not target_path.exists():
        return True
    try:
        source_stat = source_path.stat()
        target_stat = target_path.stat()
    except OSError:
        return True
    return (
        source_stat.st_size != target_stat.st_size
        or int(source_stat.st_mtime) != int(target_stat.st_mtime)
        or not filecmp.cmp(source_path, target_path, shallow=False)
    )


def ensure_runtime_layout() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    for filename in SEED_DATA_FILES:
        source_path = BUNDLE_DATA_DIR / filename
        target_path = DATA_DIR / filename
        if _should_refresh_seed(source_path, target_path):
            shutil.copy2(source_path, target_path)
