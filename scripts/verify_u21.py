#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "tests" / "fixtures" / "white-oxford-shirt.png"


def request_json(url: str, *, method: str = "GET", body: bytes | None = None, content_type: str = "application/json"):
    request = Request(url, data=body, method=method, headers={"Content-Type": content_type})
    with urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url: str, payload: dict[str, object]):
    return request_json(url, method="POST", body=json.dumps(payload).encode("utf-8"))


def connected_device() -> str | None:
    if shutil.which("xcrun"):
        result = subprocess.run(
            ["xcrun", "simctl", "list", "devices", "booted", "-j"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            devices = json.loads(result.stdout).get("devices", {})
            if any(device.get("state") == "Booted" for group in devices.values() for device in group):
                return "ios-simulator"

    if shutil.which("adb"):
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True, check=False)
        if any(line.endswith("\tdevice") for line in result.stdout.splitlines()[1:]):
            return "android"

    return None


def run_pipeline(api_base: str, fixture: Path) -> dict[str, object]:
    image_bytes = fixture.read_bytes()
    ticket = post_json(
        f"{api_base}/closet-items/uploads",
        {
            "fileName": fixture.name,
            "contentType": "image/png",
            "byteSize": len(image_bytes),
            "checksumSha256": hashlib.sha256(image_bytes).hexdigest(),
        },
    )

    origin = f"{urlparse(api_base).scheme}://{urlparse(api_base).netloc}"
    upload_url = urljoin(origin, ticket["uploadUrl"])
    request_json(upload_url, method="PUT", body=image_bytes, content_type="image/png")
    job = post_json(
        f"{api_base}/closet-items/analyze",
        {
            "uploadId": ticket["uploadId"],
            "requestedOperations": ["quality_check", "attribute_extraction", "illustration"],
        },
    )
    worker = None
    for _ in range(20):
        candidate = post_json(f"{api_base}/closet-items/jobs/process-next", {})
        if candidate.get("jobId") == job["jobId"]:
            worker = candidate
            break
        if not candidate.get("processed"):
            break
    if worker is None:
        raise RuntimeError(f"Analysis worker did not process job {job['jobId']}")
    if worker.get("status") not in {"succeeded", "needs_user_review"}:
        raise RuntimeError(f"Analysis worker failed: {worker}")
    return worker


def main() -> int:
    parser = argparse.ArgumentParser(description="Fitlog U21 device and live-provider acceptance preflight")
    parser.add_argument("--api-base", default="http://127.0.0.1:8000/api/v1")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--require-device", action="store_true")
    parser.add_argument("--require-live-provider", action="store_true")
    args = parser.parse_args()

    api_base = args.api_base.rstrip("/")
    readiness = request_json(f"{api_base}/runtime-readiness")
    print(f"[PASS] API: {api_base}")
    print(f"[PASS] Repository: {readiness['repositoryBackend']}")

    worker = run_pipeline(api_base, args.fixture)
    provider = worker["result"]["provider"]
    print(f"[PASS] Photo pipeline: {args.fixture.name} -> {worker['status']} ({provider})")

    live = bool(readiness["imageAnalysis"]["live"] and provider == "openai")
    print(f"[{'PASS' if live else 'BLOCKED'}] Live provider: {readiness['imageAnalysis']['provider']}")

    device = connected_device()
    print(f"[{'PASS' if device else 'BLOCKED'}] Device: {device or 'none detected'}")

    if args.require_live_provider and not live:
        return 2
    if args.require_device and not device:
        return 2
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        raise SystemExit(1)
