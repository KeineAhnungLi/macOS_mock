from __future__ import annotations

import json
import logging
import threading
from copy import deepcopy
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from app.runtime_paths import (
    ANSWER_KEY_PATH,
    DATA_DIR,
    EVENT_LOG_PATH,
    LOG_DIR,
    PROGRESS_PATH,
    QUESTIONS_PATH,
    STATIC_DIR,
    ensure_runtime_layout,
)

FILE_LOCK = threading.Lock()
ensure_runtime_layout()


def setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("practice_server")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    file_handler = logging.FileHandler(LOG_DIR / "server.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger


LOGGER = setup_logging()


def load_json(path, default=None):
    if not path.exists():
        return deepcopy(default)
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_dataset() -> dict:
    dataset = load_json(QUESTIONS_PATH, default={"meta": {}, "years": []}) or {"meta": {}, "years": []}
    answer_key = load_json(ANSWER_KEY_PATH, default={}) or {}
    merged = deepcopy(dataset)
    answer_count = 0

    for year_entry in merged.get("years", []):
        for question in year_entry.get("questions", []):
            answer_entry = answer_key.get(question["id"], {})
            question["correct_option"] = answer_entry.get("correct_option")
            question["explanation"] = answer_entry.get("explanation", "")
            if question["correct_option"]:
                answer_count += 1

    merged.setdefault("meta", {})
    merged["meta"]["answer_count"] = answer_count
    merged["meta"]["answer_key_loaded"] = ANSWER_KEY_PATH.exists()
    return merged


def default_progress() -> dict:
    return {
        "version": 1,
        "updated_at": None,
        "answers": {},
        "manual_wrong_book": {},
        "mock_sessions": [],
    }


def load_progress() -> dict:
    return load_json(PROGRESS_PATH, default=default_progress()) or default_progress()


def append_event(event_type: str, payload: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "payload": payload,
    }
    with FILE_LOCK:
        with EVENT_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


class PracticeHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/exams":
            self.respond_json(load_dataset())
            return
        if parsed.path == "/api/progress":
            self.respond_json(load_progress())
            return
        if parsed.path == "/api/status":
            dataset = load_dataset()
            progress = load_progress()
            payload = {
                "answer_key_loaded": dataset["meta"].get("answer_key_loaded", False),
                "answer_count": dataset["meta"].get("answer_count", 0),
                "year_count": len(dataset.get("years", [])),
                "question_count": sum(len(year_entry.get("questions", [])) for year_entry in dataset.get("years", [])),
                "progress_updated_at": progress.get("updated_at"),
            }
            self.respond_json(payload)
            return
        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length) if content_length else b"{}"

        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self.respond_json({"error": "invalid_json"}, status=HTTPStatus.BAD_REQUEST)
            return

        if parsed.path == "/api/events":
            append_event(payload.get("type", "unknown"), payload)
            self.respond_json({"ok": True})
            return

        if parsed.path == "/api/progress":
            append_event("progress_saved", {"updated_at": payload.get("updated_at")})
            with FILE_LOCK:
                save_json(PROGRESS_PATH, payload)
            self.respond_json({"ok": True})
            return

        self.respond_json({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, format: str, *args) -> None:
        LOGGER.info("%s - %s", self.address_string(), format % args)

    def respond_json(self, payload, status: HTTPStatus = HTTPStatus.OK) -> None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), PracticeHandler)
    actual_host, actual_port = server.server_address[:2]
    LOGGER.info("Site started: http://%s:%s", actual_host, actual_port)
    LOGGER.info("Static dir: %s", STATIC_DIR)
    LOGGER.info("Data dir: %s", DATA_DIR)
    LOGGER.info("Event log: %s", EVENT_LOG_PATH)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        LOGGER.info("Shutdown requested.")
    finally:
        server.server_close()
