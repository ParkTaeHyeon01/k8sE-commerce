"""기존 products 컬렉션 전체에 ngrams 필드를 추가하는 1회성 마이그레이션."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from db import get_collection
from ngram import make_ngrams


def migrate():
    col = get_collection()
    total = col.count_documents({})
    updated = 0

    for doc in col.find({}, {"_id": 1, "name": 1}):
        name = doc.get("name", "")
        if not name:
            continue
        col.update_one({"_id": doc["_id"]}, {"$set": {"ngrams": make_ngrams(name)}})
        updated += 1
        if updated % 200 == 0:
            print(f"  {updated}/{total} 완료")

    # ngrams 배열 인덱스 생성
    col.create_index("ngrams")
    print(f"마이그레이션 완료: {updated}/{total}개 문서 업데이트, ngrams 인덱스 생성")


if __name__ == "__main__":
    migrate()
