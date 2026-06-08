# 크롤러 진입점
# 흐름: trace_id 생성 -> (.env의 CRAWL_TARGET으로 선택된 컬렉션) x 식품 카테고리 순회
#       -> 카테고리별 상품 파싱 -> 로컬 JSON 저장
import asyncio
import json
import os
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from logger import get_logger
from pages import COLLECTIONS, FOOD_CATEGORIES, build_url
from parsers import kurly

# 로컬 개발 중에는 .env 파일에서, k8s에서는 ConfigMap/Secret으로 주입된 환경변수를 그대로 사용한다
load_dotenv()

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# 베스트("best") / 할인("sales") 중 어떤 컬렉션을 수집할지 환경변수로 선택한다
CRAWL_TARGET = os.environ.get("CRAWL_TARGET", "best")


async def crawl_category(page, logger, label: str, category_name: str, url: str) -> list[dict]:
    logger.info(f"수집 시작 - {label}/{category_name} ({url})")
    await page.goto(url, wait_until="domcontentloaded", timeout=50000)
    await page.wait_for_timeout(2000)

    # 컬리는 무한 스크롤 방식으로 상품을 지연 로딩하므로 스크롤로 콘텐츠를 더 불러와야 한다
    for _ in range(8):
        await page.mouse.wheel(0, 3000)
        await page.wait_for_timeout(1000)

    products = await kurly.parse_page(page)
    logger.info(f"수집 완료 - {label}/{category_name} 상품 {len(products)}건")
    return products


async def run() -> dict:
    trace_id = str(uuid.uuid4())
    crawled_at = datetime.now(timezone.utc).isoformat()
    logger = get_logger("crawler", trace_id)

    if CRAWL_TARGET not in COLLECTIONS:
        raise ValueError(f"알 수 없는 CRAWL_TARGET 값: {CRAWL_TARGET} (best 또는 sales만 가능)")

    label = COLLECTIONS[CRAWL_TARGET]["label"]
    logger.info(f"크롤링 작업 시작 - 대상: {label}, 카테고리 {len(FOOD_CATEGORIES)}개")

    results = []

    async with Stealth().use_async(async_playwright()) as p:
        # k8s 컨테이너에는 디스플레이가 없으므로 headless로 실행한다
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=USER_AGENT, locale="ko-KR")
        page = await context.new_page()

        for category_code, category_name in FOOD_CATEGORIES.items():
            url = build_url(CRAWL_TARGET, category_code)
            try:
                products = await crawl_category(page, logger, label, category_name, url)
            except Exception as e:
                logger.error(f"수집 실패 - {label}/{category_name}: {e}")
                continue

            results.append({
                "target": CRAWL_TARGET,
                "label": label,
                "category_code": category_code,
                "category_name": category_name,
                "url": url,
                "products": products,
            })

        await browser.close()

    logger.info("크롤링 작업 종료")

    return {
        "trace_id": trace_id,
        "crawled_at": crawled_at,
        "target": CRAWL_TARGET,
        "results": results,
    }


def main():
    output = asyncio.run(run())
    file_name = f"crawled_{output['target']}_{output['trace_id']}.json"
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"저장 완료: {file_name}")


if __name__ == "__main__":
    main()
