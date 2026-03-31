"""Seed a sample idea + local-only run via the API."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _request_json(
    method: str, url: str, payload: dict[str, object] | None = None
) -> dict[str, object]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = Request(url=url, method=method, data=data, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {exc.code} for {url}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Unable to reach app at {url}: {exc}") from exc


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    _load_dotenv(project_root / ".env")

    host = os.getenv("APP_HOST", "127.0.0.1")
    if host == "0.0.0.0":
        host = "127.0.0.1"
    port = os.getenv("APP_PORT", "8000")
    base_url = f"http://{host}:{port}"

    docs_dir = os.getenv("APP_DOCS_DIR", "./docs")
    docs_path = (
        (project_root / docs_dir).resolve()
        if not Path(docs_dir).is_absolute()
        else Path(docs_dir)
    )
    docs_path.mkdir(parents=True, exist_ok=True)

    idea_payload = {
        "title": "Example: AIdeator Demo Idea",
        "description": "Demo idea created by scripts/seed_example.py for local onboarding.",
        "target_user": "new-contributor",
        "context": "seed-flow",
    }
    idea_result = _request_json("POST", f"{base_url}/ideas", idea_payload)
    idea_id = str(idea_result["idea_id"])

    run_result = _request_json(
        "POST",
        f"{base_url}/runs",
        {"idea_id": idea_id, "tier": "low", "mode": "local-only"},
    )
    run_id = str(run_result["run_id"])

    status = "pending"
    deadline = time.time() + 30.0
    while time.time() < deadline:
        status_payload = _request_json("GET", f"{base_url}/runs/{run_id}/status")
        status = str(status_payload.get("status", "pending"))
        if status in {"succeeded", "failed"}:
            break
        time.sleep(0.3)

    _request_json("POST", f"{base_url}/internal/rebuild-docs", {})
    report_path = docs_path / f"idea-{idea_id}.md"
    if not report_path.exists():
        raise RuntimeError(
            f"Expected markdown artifact not found at {report_path}. "
            "Run POST /internal/rebuild-docs or verify docs generation path."
        )

    print(f"Idea ID: {idea_id}")
    print(f"Run ID: {run_id}")
    print(f"Run Status: {status}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
