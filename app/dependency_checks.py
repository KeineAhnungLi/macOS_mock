from __future__ import annotations

import os
import platform
import subprocess
import sys
import tempfile
import webbrowser
from pathlib import Path

from app.runtime_paths import DATA_DIR, QUESTIONS_PATH

MIN_SOURCE_PYTHON = (3, 10)
MAC_CHROME_CANDIDATES = (
    Path("/Applications/Google Chrome.app"),
    Path.home() / "Applications" / "Google Chrome.app",
)


def _frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _python_status() -> dict:
    version = platform.python_version()
    if _frozen():
        return {
            "ok": True,
            "bundled": True,
            "version": version,
            "minimum": None,
            "message": "Bundled runtime available.",
        }

    ok = sys.version_info >= MIN_SOURCE_PYTHON
    minimum = ".".join(str(part) for part in MIN_SOURCE_PYTHON)
    return {
        "ok": ok,
        "bundled": False,
        "version": version,
        "minimum": minimum,
        "message": f"Source mode requires Python {minimum}+.",
    }


def _chrome_path() -> Path | None:
    if sys.platform != "darwin":
        return None
    for candidate in MAC_CHROME_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def _browser_status() -> dict:
    chrome_path = _chrome_path()
    return {
        "ok": True,
        "preferred": "chrome" if chrome_path else "default",
        "chrome_found": bool(chrome_path),
        "chrome_path": str(chrome_path) if chrome_path else None,
        "message": "Chrome found." if chrome_path else "Chrome not found; default browser fallback will be used.",
    }


def _writable_directory_status() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.NamedTemporaryFile(dir=DATA_DIR, prefix="tem8-check-", delete=True):
            pass
        return {"ok": True, "path": str(DATA_DIR), "message": "Data directory is writable."}
    except OSError as error:
        return {"ok": False, "path": str(DATA_DIR), "message": f"Data directory is not writable: {error}"}


def _questions_status() -> dict:
    ok = QUESTIONS_PATH.exists()
    return {
        "ok": ok,
        "path": str(QUESTIONS_PATH),
        "message": "questions.json found." if ok else "questions.json is missing.",
    }


def collect_runtime_diagnostics() -> dict:
    python_status = _python_status()
    browser_status = _browser_status()
    data_dir_status = _writable_directory_status()
    questions_status = _questions_status()
    return {
        "platform": sys.platform,
        "platform_version": platform.platform(),
        "frozen": _frozen(),
        "python": python_status,
        "browser": browser_status,
        "data_dir": data_dir_status,
        "questions": questions_status,
        "fatal": not (python_status["ok"] and data_dir_status["ok"] and questions_status["ok"]),
    }


def print_runtime_diagnostics(as_json: bool = False) -> int:
    diagnostics = collect_runtime_diagnostics()
    if as_json:
        import json

        print(json.dumps(diagnostics, ensure_ascii=False, indent=2))
    else:
        print(f"Platform: {diagnostics['platform_version']}")
        print(f"Frozen: {diagnostics['frozen']}")
        print(f"Python: {diagnostics['python']['version']} ({diagnostics['python']['message']})")
        print(f"Browser: {diagnostics['browser']['message']}")
        print(f"Questions: {diagnostics['questions']['message']}")
        print(f"Data dir: {diagnostics['data_dir']['message']}")
        print(f"Fatal issues: {'yes' if diagnostics['fatal'] else 'no'}")
    return 1 if diagnostics["fatal"] else 0


def open_url(url: str) -> None:
    chrome_path = _chrome_path()
    if chrome_path:
        try:
            subprocess.Popen(["open", "-a", str(chrome_path), url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        except OSError:
            pass
    webbrowser.open(url, new=2)
