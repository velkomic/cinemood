"""Deterministic OpenAI HTTP boundary for tests and the offline demo only."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class EmbeddingHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
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

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 18080), EmbeddingHandler).serve_forever()
