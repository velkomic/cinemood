"""Collect the frozen evaluation once; judgments are recorded separately by a human.

Run against the local app already configured for the reviewed real catalog.
No credentials are accepted or written by this runner. No retries or ingestion.
"""

import argparse
import json
import time
from pathlib import Path

import httpx

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--url", default="http://127.0.0.1:58005")
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--cases", type=Path, default=Path("evaluation/requests.json"))
args = parser.parse_args()
if args.output.exists():
    parser.error("Output already exists; preserve the original evaluation.")
requests = json.loads(args.cases.read_text())
if not 1 <= len(requests) <= 20:
    parser.error("An evaluation must contain 1–20 fixed cases.")
args.output.parent.mkdir(parents=True, exist_ok=True)
# Published standard USD rates; report estimates, not settled invoices.
# Recheck rates before a future run. No cache discounts are assumed.
cumulative_cost = 0.0
with args.output.open("x") as artifact, httpx.Client(timeout=85) as client:
    for case in requests:
        # Fixed run: <=20 requests, <=80 chat calls, no retries. Stop on an
        # observed USD 0.50 estimate; interrupted usage may not be accounted for.
        if cumulative_cost >= 0.5:
            break
        started = time.monotonic()
        events = []
        received = {
            "first_status": None,
            "first_movie": None,
            "first_explanation": None,
        }
        failure = None
        response_status = None
        frame = []
        try:
            with client.stream(
                "POST",
                args.url + "/api/recommendations/stream",
                json={"request": case["request"]},
            ) as response:
                response_status = response.status_code
                response.raise_for_status()
                frame = []
                for line in response.iter_lines():
                    if line:
                        frame.append(line)
                        continue
                    if not frame:
                        continue
                    event = frame[0].removeprefix("event: ")
                    data = json.loads(frame[1].removeprefix("data: "))
                    events.append({"event": event, "data": data})
                    frame = []
                    key = {
                        "status": "first_status",
                        "explanation_delta": "first_explanation",
                    }.get(event)
                    if event == "result" and data.get("movies"):
                        key = "first_movie"
                    if key and received[key] is None:
                        received[key] = round((time.monotonic() - started) * 1000, 2)
            if frame or not events or events[-1]["event"] not in ("complete", "error"):
                failure = {"kind": "IncompleteStream"}
        except (httpx.HTTPError, ValueError, IndexError, KeyError) as exc:
            failure = {"kind": type(exc).__name__}
        except KeyboardInterrupt:
            failure = {"kind": "Interrupted"}
        received["total"] = round((time.monotonic() - started) * 1000, 2)
        terminal = events[-1]["data"] if events else {}
        calls = terminal.get("provider_calls", [])
        cost = 0.0
        accounting_complete = (
            failure is None and bool(events) and events[-1]["event"] == "complete"
        )
        for call in calls:
            tokens = call["tokens"]
            if tokens is None:
                accounting_complete = False
                continue
            rate_in, rate_out = (
                (0.02, 0) if call["stage"] == "query_embedding" else (0.75, 4.5)
            )
            cost += (
                tokens["input_tokens"] * rate_in + tokens["output_tokens"] * rate_out
            ) / 1_000_000
        cumulative_cost += cost
        artifact.write(
            json.dumps(
                {
                    **case,
                    "events": events,
                    "client_timings_ms": received,
                    "estimated_usd_no_cache_discount": cost,
                    "accounting_complete": accounting_complete,
                    "human_judgment": None,
                    "failure": failure,
                    "http_status": response_status,
                    "partial_frame": frame,
                }
            )
            + "\n"
        )
        artifact.flush()
        print(
            f"Case {case['id']}: {events[-1]['event'] if events else 'EOF'}, "
            f"{received['total']} ms; cumulative estimate USD {cumulative_cost:.6f}",
            flush=True,
        )
        if failure is not None:
            # Preserve the attempted case before stopping; do not retry it or
            # replace the failed run with a later successful sample.
            break
