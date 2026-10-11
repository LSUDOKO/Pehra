"""Preview Pehra's public website locally, without AWS or sending any messages.

    python scripts/preview_web.py --port 8765
"""

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

WEB = Path(__file__).resolve().parents[1] / "web"
ROUTES = {
    "/": "/home/index.html",
    "/audit": "/audit/index.html",
    "/model-card": "/model_card/index.html",
    "/site.css": "/india.css",
    "/assets/gsap.min.js": "/vendor/gsap-3.13.0.min.js",
    "/assets/ScrollTrigger.min.js": "/vendor/ScrollTrigger-3.13.0.min.js",
}


class PreviewHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    def do_GET(self):
        self.path = ROUTES.get(urlsplit(self.path).path, self.path)
        super().do_GET()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), PreviewHandler)
    print(f"Pehra preview: http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
