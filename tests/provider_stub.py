"""Deterministic OpenAI HTTP boundary for tests and the offline demo only."""

import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock


class OpenAIHandler(BaseHTTPRequestHandler):
    interpretations = {}
    calls = []
    explanations = {}
    active_streams = 0
    stream_lock = Lock()

    def do_POST(self):
        self.calls.append(self.path)
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if body.get("stream"):
            with self.stream_lock:
                type(self).active_streams += 1
            try:
                self.stream_explanation(body)
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                with self.stream_lock:
                    type(self).active_streams -= 1
            return
        if "messages" in body:
            request = body["messages"][-1]["content"]
            interpretation = {
                "semantic_query": request,
                "included_genres": [],
                "excluded_genres": [],
                "runtime_minutes": None,
                "runtime_operator": None,
                "year_min": None,
                "year_max": None,
                "original_language": None,
                "unsupported_requirements": [],
                "clarification": [],
            }
            if request == "quiet comfort under 92 minutes":
                interpretation.update(runtime_minutes=92, runtime_operator="lt")
            overrides = dict(self.interpretations.get(request, {}))
            http_status = overrides.pop("_http_status", None)
            if http_status:
                self.send_response(http_status)
                self.end_headers()
                self.wfile.write(b'{"error":{"message":"fixture extraction outage"}}')
                return
            omit = overrides.pop("_omit", None)
            refusal = overrides.pop("_refusal", None)
            finish_reason = overrides.pop("_finish_reason", "stop")
            content = overrides.pop("_content", None)
            interpretation.update(overrides)
            if omit:
                interpretation.pop(omit)
            content = content if content is not None else json.dumps(interpretation)
            result = json.dumps(
                {
                    "id": "chat-fixture",
                    "object": "chat.completion",
                    "created": 1,
                    "model": body["model"],
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": content,
                                "refusal": refusal,
                            },
                            "finish_reason": finish_reason,
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 10,
                        "total_tokens": 20,
                    },
                }
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(result)))
            self.end_headers()
            self.wfile.write(result)
            return
        inputs = body["input"]
        if isinstance(inputs, str):
            inputs = [inputs]
        if any("provider failure" in text for text in inputs):
            self.send_response(503)
            self.end_headers()
            self.wfile.write(b'{"error":{"message":"fixture outage"}}')
            return
        data = []
        for index, text in enumerate(inputs):
            if "Lantern Kitchen" in text:
                head = [1.0, 0.0]
            elif "Garden Letters" in text:
                head = [0.8, 0.6]
            elif "River Workshop" in text:
                head = [0.6, 0.8]
            elif "Orbital Rescue" in text or "space" in text:
                head = [0.0, 1.0]
            else:
                head = [1.0, 0.0]
            vector = head + [0.0] * 1534
            if "equal distance" in text:
                vector = [0.0, 0.0, 1.0] + [0.0] * 1533
            if "invalid vector" in text:
                vector = [0.0] * 1536
            if "wrong dimensions" in text:
                vector = [1.0, 0.0]
            data.append({"object": "embedding", "index": index, "embedding": vector})
        result = json.dumps(
            {
                "object": "list",
                "data": data,
                "model": body["model"],
                "usage": {"prompt_tokens": 10, "total_tokens": 10},
            }
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(result)))
        self.end_headers()
        self.wfile.write(result)

    def stream_explanation(self, body):
        context = json.loads(body["messages"][-1]["content"])
        movie = context["movie"]
        overrides = dict(self.explanations.get(context["mood_themes"], {}))
        quote_evidence = overrides.pop("_quote_evidence", False)
        finish = overrides.pop("_finish", "stop")
        raw = overrides.pop("_raw", None)
        delay = overrides.pop("_delay", 0)
        http_status = overrides.pop("_http_status", None)
        if http_status:
            self.send_response(http_status)
            self.end_headers()
            return
        output = {
            "movie_id": movie["id"],
            "explanation": "This may fit your request: " + movie["overview"],
            "evidence": [movie["overview"]],
        }
        output.update(overrides)
        if quote_evidence:
            output["evidence"] = ['"' + quote + '"' for quote in output["evidence"]]
        output = raw if raw is not None else json.dumps(output, ensure_ascii=False)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for start in range(0, len(output), 12):
            time.sleep(delay)
            self.wfile.write(
                (
                    "data: "
                    + json.dumps(
                        {
                            "id": "explanation-fixture",
                            "object": "chat.completion.chunk",
                            "created": 1,
                            "model": body["model"],
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {
                                        "role": "assistant",
                                        "content": output[start : start + 12],
                                    },
                                    "finish_reason": None,
                                }
                            ],
                        }
                    )
                    + "\n\n"
                ).encode()
            )
            self.wfile.flush()
        self.wfile.write(
            (
                "data: "
                + json.dumps(
                    {
                        "id": "explanation-fixture",
                        "object": "chat.completion.chunk",
                        "created": 1,
                        "model": body["model"],
                        "choices": [{"index": 0, "delta": {}, "finish_reason": finish}],
                        "usage": {
                            "prompt_tokens": 100,
                            "completion_tokens": 50,
                            "total_tokens": 150,
                        },
                    }
                )
                + "\n\ndata: [DONE]\n\n"
            ).encode()
        )
        self.wfile.flush()

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 18080), OpenAIHandler).serve_forever()
