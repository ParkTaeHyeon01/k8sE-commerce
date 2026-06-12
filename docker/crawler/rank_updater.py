"""
인기순 업데이트 전용 크롤러 — 목록 페이지 순서만 수집해 MongoDB rank 갱신
스크롤 대신 page 파라미터 순회로 최대 MAX_PAGES × 96개의 전체 순위를 수집한다
k8s CronJob으로 1~2시간마다 실행해 인기순을 주기적으로 최신화한다
"""
import asyncio
import os
import re
import uuid
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from pymongo import MongoClient, UpdateOne

load_dotenv(Path(__file__).parent.parent / ".env")

from logger import get_logger

_GOODS_ID_PATTERN = re.compile(r"/goods/(\d+)")
_MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
_MONGODB_DB  = os.environ.get("MONGODB_DB", "ecommerce")

CRAWL_TARGET = os.environ.get("CRAWL_TARGET", "best")
MAX_PAGES    = int(os.environ.get("RANK_MAX_PAGES", "0"))  # 0 = 제한 없음 (페이지 소진까지)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# 카테고리 필터 없이 전체 판매량순 URL — page 파라미터는 동적으로 붙인다
_RANK_BASE_URLS = {
    "best":  "https://www.kurly.com/collection-groups/market-best?site=MARKET&collection=market-best-logic&per_page=96&sorted_type=1",
    "sales": "https://www.kurly.com/collection-groups/market-sales-group?site=MARKET&collection=market-sales-main1&per_page=96&sorted_type=1",
}

_LABELS = {"best": "베스트", "sales": "할인"}


async def fetch_ranked_ids(page, url: str) -> list[str]:
    """목록 페이지 한 장에서 article 순서대로 product_id 리스트를 반환한다."""
    await page.goto(url, wait_until="domcontentloaded", timeout=50000)
    await page.wait_for_timeout(2000)

    hrefs = await page.locator("article").evaluate_all(
        "cards => cards.map(c => { const a = c.querySelector('a[href*=\"/goods/\"]'); return a ? a.getAttribute('href') : null; })"
    )

    seen = set()
    ranked = []
    for href in hrefs:
        m = _GOODS_ID_PATTERN.search(href or "")
        if m:
            pid = m.group(1)
            if pid not in seen:
                seen.add(pid)
                ranked.append(pid)
    return ranked


def bulk_update_ranks(collection, target: str, product_ids: list[str], start_rank: int = 1) -> int:
    """product_id 리스트 순서대로 best_rank / sales_rank 를 MongoDB에 일괄 갱신한다."""
    rank_field = f"{target}_rank"
    ops = [
        UpdateOne({"product_id": pid}, {"$set": {rank_field: rank}})
        for rank, pid in enumerate(product_ids, start=start_rank)
    ]
    if not ops:
        return 0
    result = collection.bulk_write(ops, ordered=False)
    return result.matched_count


async def run() -> None:
    trace_id = str(uuid.uuid4())
    logger = get_logger("rank-updater", trace_id)

    if CRAWL_TARGET not in _RANK_BASE_URLS:
        raise ValueError(f"알 수 없는 CRAWL_TARGET: {CRAWL_TARGET}")

    label = _LABELS[CRAWL_TARGET]
    limit_msg = f"최대 {MAX_PAGES}페이지" if MAX_PAGES > 0 else "전체 페이지"
    logger.info(f"순위 업데이트 시작 - 대상: {label}, {limit_msg} × 96개")

    client = MongoClient(_MONGODB_URI)
    collection = client[_MONGODB_DB]["products"]

    # 이전 순위(카테고리별 방식 등 구방식 포함) 전부 초기화 후 새 순위 입력
    rank_field = f"{CRAWL_TARGET}_rank"
    cleared = collection.update_many({"targets": CRAWL_TARGET}, {"$unset": {rank_field: ""}})
    logger.info(f"기존 순위 초기화 - {cleared.modified_count}건")

    total_collected = 0
    total_updated = 0

    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"])
        ctx = await browser.new_context(user_agent=USER_AGENT, locale="ko-KR")
        page = await ctx.new_page()

        page_num = 1
        while MAX_PAGES == 0 or page_num <= MAX_PAGES:
            url = f"{_RANK_BASE_URLS[CRAWL_TARGET]}&page={page_num}"
            try:
                ids = await fetch_ranked_ids(page, url)
                if not ids:
                    logger.info(f"페이지 {page_num}: 상품 없음 — 수집 종료")
                    break
                # 이 페이지 상품의 전역 시작 순위 = 이전까지 누적 수 + 1
                page_start_rank = total_collected + 1
                updated = bulk_update_ranks(collection, CRAWL_TARGET, ids, start_rank=page_start_rank)
                total_collected += len(ids)
                total_updated += updated
                logger.info(f"페이지 {page_num}: {len(ids)}건 수집·갱신 (누적 {total_collected}건)")
            except Exception as e:
                logger.error(f"페이지 {page_num} 수집 실패: {e}")
                break
            page_num += 1

        await browser.close()

    client.close()
    logger.info(f"순위 업데이트 종료 - 총 {total_collected}건 수집, {total_updated}건 갱신")


if __name__ == "__main__":
    asyncio.run(run())
