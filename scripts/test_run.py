"""Test a full hybrid run (LLM + Search)."""

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
        with urlopen(req, timeout=30) as resp: # Longer timeout for LLM/Search
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

    print(f"Starting E2E Smoke Test at {base_url}...")

    # 1. Create Idea
    idea_payload = {
        "title": "Hybrid-Ready AI Tool",
        "description": "A proof-of-concept for hybrid search and LLM synthesis.",
        "target_user": "AI Researchers",
        "context": "testing-hybrid-flow",
    }
    print("Creating Idea...")
    idea_result = _request_json("POST", f"{base_url}/ideas", idea_payload)
    idea_id = str(idea_result["idea_id"])
    print(f"  [OK] Idea ID: {idea_id}")

    # 2. Start Hybrid Run
    print("Starting Hybrid Run (LLM + DDG)...")
    run_result = _request_json(
        "POST",
        f"{base_url}/runs",
        {"idea_id": idea_id, "tier": "low", "mode": "hybrid"},
    )
    run_id = str(run_result["run_id"])
    print(f"  [OK] Run ID: {run_id}")

    # 3. Poll for Success
    print("Polling status (this may take 20-60s)...")
    status = "pending"
    deadline = time.time() + 120.0 # 2 minute timeout
    while time.time() < deadline:
        status_payload = _request_json("GET", f"{base_url}/runs/{run_id}/status")
        status = str(status_payload.get("status", "pending"))
        print(f"  Current Status: {status}")
        if status in {"succeeded", "failed"}:
            break
        time.sleep(2.0)

    if status == "succeeded":
        print("\n[SUCCESS] Pipeline completed.")
        # Rebuild docs to be sure
        _request_json("POST", f"{base_url}/internal/rebuild-docs", {})
        
        # Verify markdown file
        docs_dir = os.getenv("APP_DOCS_DIR", "./docs")
        report_path = project_root / docs_dir / f"idea-{idea_id}.md"
        if report_path.exists():
            print(f"  [OK] Report found at: {report_path}")
            print(f"  [OK] Preview: {report_path.read_text()[:100]}...")
        else:
            print(f"  [!] Report MISSING at: {report_path}")
    else:
        print(f"\n[FAILED] Pipeline status: {status}")


if __name__ == "__main__":
    main()
