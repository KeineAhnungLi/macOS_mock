from __future__ import annotations

import argparse
import socket
import threading

from app.dependency_checks import open_url, print_runtime_diagnostics
from app.runtime_paths import LOG_DIR, QUESTIONS_PATH, ensure_runtime_layout
from app.server import serve


def choose_port(host: str, preferred_port: int) -> int:
    candidates = [preferred_port + offset for offset in range(0, 10)]
    candidates.append(0)

    for candidate in candidates:
        with socket.socket() as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind((host, candidate))
            except OSError:
                continue
            return probe.getsockname()[1]

    raise RuntimeError("No available local port was found.")


def access_urls(host: str, port: int) -> list[str]:
    if host not in {"0.0.0.0", "::"}:
        return [f"http://{host}:{port}"]

    urls = [f"http://127.0.0.1:{port}"]
    candidates = set()
    try:
        hostname = socket.gethostname()
        for family, *_rest, sockaddr in socket.getaddrinfo(hostname, None, family=socket.AF_INET):
            if family == socket.AF_INET:
                ip = sockaddr[0]
                if ip and not ip.startswith("127."):
                    candidates.add(ip)
    except OSError:
        pass

    for ip in sorted(candidates):
        urls.append(f"http://{ip}:{port}")
    return urls


def open_browser_later(url: str, delay_seconds: float = 1.0) -> None:
    timer = threading.Timer(delay_seconds, lambda: open_url(url))
    timer.daemon = True
    timer.start()


def main() -> None:
    parser = argparse.ArgumentParser(description="Local gateway for the TEM-8 practice site.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--self-check-json", action="store_true")
    args = parser.parse_args()

    ensure_runtime_layout()
    if not QUESTIONS_PATH.exists():
        raise SystemExit(
            "questions.json was not found. Run `python run.py --extract-only` first, or keep the bundled data folder next to the exe."
        )
    if args.self_check or args.self_check_json:
        raise SystemExit(print_runtime_diagnostics(as_json=args.self_check_json))

    port = choose_port(args.host, args.port)
    urls = access_urls(args.host, port)
    url = urls[0]
    print(f"Gateway ready: {url}")
    print(f"Logs: {LOG_DIR}")
    if len(urls) > 1:
        print("Accessible URLs:")
        for item in urls:
            print(f"  {item}")
        print("For shared browser use, append ?progress=local to keep progress in each browser.")

    if not args.no_browser:
        open_browser_later(url)

    serve(host=args.host, port=port)


if __name__ == "__main__":
    main()
