import os
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from pymongo import MongoClient

_MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
_MONGODB_DB  = os.environ.get("MONGODB_DB", "ecommerce")

_client = MongoClient(_MONGODB_URI)
_col    = _client[_MONGODB_DB]["products"]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed    = urlparse(self.path)
        params    = parse_qs(parsed.query)
        target    = params.get("target",    ["best"])[0]
        page      = int(params.get("page",      [1])[0])
        page_size = int(params.get("page_size", [20])[0])

        pipeline = [
            {"$match": {"status": "ready", "targets": target}},
            {"$project": {"detail_blocks": 0, "ngrams": 0, "_id": 0}},
            {"$facet": {
                "total":    [{"$count": "n"}],
                "products": [
                    {"$skip":  (page - 1) * page_size},
                    {"$limit": page_size},
                ],
            }},
        ]
        result = list(_col.aggregate(pipeline))
        total  = result[0]["total"][0]["n"] if result and result[0]["total"] else 0
        docs   = result[0]["products"] if result else []

        body = json.dumps({"products": docs, "total": total, "page": page, "page_size": page_size}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8000), Handler)
    print("REST 서버 시작 - 포트 8000")
    server.serve_forever()
