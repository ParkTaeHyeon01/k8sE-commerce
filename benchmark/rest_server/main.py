import os
import uvicorn
from fastapi import FastAPI
from pymongo import MongoClient

app = FastAPI()

_MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
_MONGODB_DB  = os.environ.get("MONGODB_DB", "ecommerce")

_client = MongoClient(_MONGODB_URI)
_col    = _client[_MONGODB_DB]["products"]


@app.get("/products")
def list_products(target: str = "best", page: int = 1, page_size: int = 20):
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
    return {"products": docs, "total": total, "page": page, "page_size": page_size}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
