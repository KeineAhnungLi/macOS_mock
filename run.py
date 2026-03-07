from __future__ import annotations

import argparse

from app.server import serve
from scripts.extract_questions import QUESTIONS_PATH, build_dataset, find_pdf


def needs_refresh() -> bool:
    if not QUESTIONS_PATH.exists():
        return True
    pdf_path = find_pdf()
    return pdf_path.stat().st_mtime > QUESTIONS_PATH.stat().st_mtime


def main() -> None:
    parser = argparse.ArgumentParser(description="OCR extractor and local server for the TEM-8 practice site.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--extract-only", action="store_true")
    args = parser.parse_args()

    if needs_refresh() or args.extract_only:
        build_dataset()

    if not args.extract_only:
        serve(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
