# 크롤러 진입점
# 흐름: trace_id 생성 -> 대상 페이지(베스트/할인) 순회 -> 상품 파싱 -> 로컬 JSON 저장
import asyncio
import json
import uuid
from datetime import datetime, timezone

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from logger import get_logger
from pages import PAGES
from parsers import kurly

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


async def crawl_page(page, logger, label: str, url: str) -> list[dict]:
    logger.info(f"수집 시작 - {label} ({url})")
    await page.goto(url, wait_until="domcontentloaded", timeout=50000)
    await page.wait_for_timeout(2000)

    # 컬리는 무한 스크롤 방식으로 상품을 지연 로딩하므로 스크롤로 콘텐츠를 더 불러와야 한다
    for _ in range(8):
        await page.mouse.wheel(0, 3000)
        await page.wait_for_timeout(1000)

    products = await kurly.parse_page(page)
    logger.info(f"수집 완료 - {label} 상품 {len(products)}건")
    return products


async def run() -> dict:
    trace_id = str(uuid.uuid4())
    crawled_at = datetime.now(timezone.utc).isoformat()
    logger = get_logger("crawler", trace_id)
    logger.info("크롤링 작업 시작")

    results = []

    async with Stealth().use_async(async_playwright()) as p:
        # k8s 컨테이너에는 디스플레이가 없으므로 headless로 실행한다
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=USER_AGENT, locale="ko-KR")
        page = await context.new_page()

        for page_key, info in PAGES.items():
            try:
                products = await crawl_page(page, logger, info["label"], info["url"])
            except Exception as e:
                logger.error(f"수집 실패 - {info['label']}: {e}")
                continue

            results.append({
                "page_key": page_key,
                "label": info["label"],
                "url": info["url"],
                "products": products,
            })

        await browser.close()

    logger.info("크롤링 작업 종료")

    return {
        "trace_id": trace_id,
        "crawled_at": crawled_at,
        "results": results,
    }


def main():
    output = asyncio.run(run())
    file_name = f"crawled_{output['trace_id']}.json"
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"저장 완료: {file_name}")


if __name__ == "__main__":
    main()
