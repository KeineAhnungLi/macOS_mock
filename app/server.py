from __future__ import annotations

import json
import logging
import os
import re
import threading
from copy import deepcopy
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

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
CLIENT_PROGRESS_DIR = DATA_DIR / "clients"
ALLOWED_ORIGINS = tuple(
    origin.strip() for origin in os.getenv("TEM8_ALLOWED_ORIGINS", "*").split(",") if origin.strip()
)
ALLOW_ALL_ORIGINS = not ALLOWED_ORIGINS or "*" in ALLOWED_ORIGINS
CLIENT_ID_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


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


def normalize_client_id(raw_value: str | None) -> str | None:
    text = str(raw_value or "").strip()
    if not text:
        return None
    text = CLIENT_ID_PATTERN.sub("-", text).strip("._-")
    if not text:
        return None
    return text[:80]


def progress_path_for_client(client_id: str | None):
    if not client_id:
        return PROGRESS_PATH
    return CLIENT_PROGRESS_DIR / f"{client_id}.json"


def origin_allowed(origin: str | None) -> bool:
    if not origin:
        return True
    return ALLOW_ALL_ORIGINS or origin in ALLOWED_ORIGINS


def load_dataset() -> dict:
    dataset = load_json(QUESTIONS_PATH, default={"meta": {}, "years": []}) or {"meta": {}, "years": []}
    answer_key = load_json(ANSWER_KEY_PATH, default={}) or {}
    merged = deepcopy(dataset)
    answer_count = 0

    for bucket_name in ("years", "library", "exercise_sets"):
        for entry in merged.get(bucket_name, []):
            for question in entry.get("questions", []):
                answer_entry = answer_key.get(question["id"], {})
                question["correct_option"] = answer_entry.get("correct_option")
                question["explanation"] = answer_entry.get("explanation", "")
                question["accepted_answers"] = answer_entry.get("accepted_answers", [])
                question["display_answer"] = answer_entry.get("display_answer", "")
                if question["correct_option"] or question["accepted_answers"] or question["display_answer"]:
                    answer_count += 1

    merged.setdefault("meta", {})
    merged["meta"]["answer_count"] = answer_count
    merged["meta"]["answer_key_loaded"] = ANSWER_KEY_PATH.exists()
    return merged


def dataset_question_count(dataset: dict) -> int:
    total = 0
    for bucket_name in ("years", "library", "exercise_sets"):
        total += sum(len(entry.get("questions", [])) for entry in dataset.get(bucket_name, []))
    return total


def default_progress() -> dict:
    return {
        "version": 1,
        "updated_at": None,
        "answers": {},
        "manual_wrong_book": {},
        "mock_sessions": [],
    }


def load_progress(client_id: str | None = None) -> dict:
    path = progress_path_for_client(client_id)
    return load_json(path, default=default_progress()) or default_progress()


def append_event(event_type: str, payload: dict, client_id: str | None = None) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "payload": payload,
    }
    if client_id:
        entry["client_id"] = client_id
    with FILE_LOCK:
        with EVENT_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


class PracticeHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def request_origin(self) -> str | None:
        return self.headers.get("Origin")

    def cors_origin_value(self) -> str | None:
        origin = self.request_origin()
        if not origin or not origin_allowed(origin):
            return None
        return "*" if ALLOW_ALL_ORIGINS else origin

    def request_client_id(self, parsed) -> str | None:
        header_value = self.headers.get("X-TEM8-Client-ID")
        query_value = parse_qs(parsed.query).get("client_id", [None])[0]
        return normalize_client_id(header_value or query_value)

    def enforce_api_origin(self) -> bool:
        origin = self.request_origin()
        if origin_allowed(origin):
            return True
        self.respond_json({"error": "origin_not_allowed"}, status=HTTPStatus.FORBIDDEN)
        return False

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        client_id = self.request_client_id(parsed)
        if parsed.path == "/api/exams":
            if not self.enforce_api_origin():
                return
            self.respond_json(load_dataset())
            return
        if parsed.path == "/api/progress":
            if not self.enforce_api_origin():
                return
            self.respond_json(load_progress(client_id))
            return
        if parsed.path == "/api/status":
            if not self.enforce_api_origin():
                return
            dataset = load_dataset()
            progress = load_progress(client_id)
            payload = {
                "answer_key_loaded": dataset["meta"].get("answer_key_loaded", False),
                "answer_count": dataset["meta"].get("answer_count", 0),
                "year_count": len(dataset.get("years", [])),
                "library_set_count": len(dataset.get("library", [])),
                "exercise_set_count": len(dataset.get("exercise_sets", [])),
                "question_count": dataset_question_count(dataset),
                "progress_updated_at": progress.get("updated_at"),
            }
            self.respond_json(payload)
            return
        super().do_GET()

    def do_OPTIONS(self) -> None:
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/"):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not self.enforce_api_origin():
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        client_id = self.request_client_id(parsed)
        if parsed.path.startswith("/api/") and not self.enforce_api_origin():
            return
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length) if content_length else b"{}"

        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self.respond_json({"error": "invalid_json"}, status=HTTPStatus.BAD_REQUEST)
            return

        if parsed.path == "/api/events":
            append_event(payload.get("type", "unknown"), payload, client_id=client_id)
            self.respond_json({"ok": True})
            return

        if parsed.path == "/api/progress":
            append_event("progress_saved", {"updated_at": payload.get("updated_at")}, client_id=client_id)
            with FILE_LOCK:
                save_json(progress_path_for_client(client_id), payload)
            self.respond_json({"ok": True})
            return

        self.respond_json({"error": "not_found"}, status=HTTPStatus.NOT_FOUND)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        if self.path.startswith("/api/"):
            cors_origin = self.cors_origin_value()
            if cors_origin:
                self.send_header("Access-Control-Allow-Origin", cors_origin)
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type, X-TEM8-Client-ID")
                self.send_header("Access-Control-Max-Age", "86400")
                self.send_header("Vary", "Origin")
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
    LOGGER.info("Allowed origins: %s", "*" if ALLOW_ALL_ORIGINS else ", ".join(ALLOWED_ORIGINS))
    LOGGER.info("Event log: %s", EVENT_LOG_PATH)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        LOGGER.info("Shutdown requested.")
    finally:
        server.server_close()
