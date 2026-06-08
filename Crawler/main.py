# 크롤러 진입점
# 흐름: trace_id 생성 -> 카테고리 그룹/코드 순회 -> 페이지 파싱 -> Kafka 전송 (+ 로컬 JSON 백업 저장)
import asyncio
import json
import uuid
from datetime import datetime, timezone

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from categories import CATEGORY_GROUPS, build_url
from logger import get_logger
from parsers import discount, popular
from producer import create_producer, send_product

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

PARSERS = {
    "popular_products": popular,
    "discount_products": discount,
}


def build_message(trace_id: str, crawled_at: str, group_key: str, category_code: str, category_name: str, product: dict) -> dict:
    """상품 1건을 Kafka 메시지(JSON)로 변환한다. trace_id를 포함해 끝까지 추적 가능하게 한다."""
    return {
        "trace_id": trace_id,
        "crawled_at": crawled_at,
        "group": group_key,
        "category_code": category_code,
        "category_name": category_name,
        **product,
    }


async def crawl_category(page, logger, group_key: str, category_code: str, category_name: str) -> list[dict]:
    url = build_url(group_key, category_code)
    parser = PARSERS[group_key]

    logger.info(f"수집 시작 - {group_key}/{category_name} ({url})")
    await page.goto(url, wait_until="networkidle", timeout=50000)
    await page.wait_for_timeout(2000)

    # 할인상품 페이지는 지연 로딩이라 스크롤로 콘텐츠를 더 불러와야 한다
    if group_key == "discount_products":
        for _ in range(8):
            await page.mouse.wheel(0, 3000)
            await page.wait_for_timeout(1000)

    products = await parser.parse_page(page)
    logger.info(f"수집 완료 - {group_key}/{category_name} 상품 {len(products)}건")
    return products


async def run() -> dict:
    trace_id = str(uuid.uuid4())
    crawled_at = datetime.now(timezone.utc).isoformat()
    logger = get_logger("crawler", trace_id)
    logger.info("크롤링 작업 시작")

    producer = create_producer()
    results = []
    sent_count = 0

    async with Stealth().use_async(async_playwright()) as p:
        # k8s 컨테이너에는 디스플레이가 없으므로 headless로 실행한다 (G마켓은 headless에서도 정상 동작 확인됨)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=USER_AGENT, locale="ko-KR")
        page = await context.new_page()

        for group_key, group_info in CATEGORY_GROUPS.items():
            for category_code, category_name in group_info["categories"].items():
                try:
                    products = await crawl_category(page, logger, group_key, category_code, category_name)
                except Exception as e:
                    logger.error(f"수집 실패 - {group_key}/{category_name}: {e}")
                    continue

                for product in products:
                    message = build_message(trace_id, crawled_at, group_key, category_code, category_name, product)
                    send_product(producer, message)
                    sent_count += 1

                results.append({
                    "group": group_key,
                    "category_code": category_code,
                    "category_name": category_name,
                    "url": build_url(group_key, category_code),
                    "products": products,
                })

        await browser.close()

    producer.flush()
    producer.close()
    logger.info(f"Kafka 전송 완료 - 총 {sent_count}건")
    logger.info("크롤링 작업 종료")

    return {
        "trace_id": trace_id,
        "crawled_at": crawled_at,
        "results": results,
    }


def main():
    output = asyncio.run(run())
    # Kafka로 전송한 데이터를 로컬에서도 확인할 수 있도록 JSON 백업을 남긴다
    file_name = f"crawled_{output['trace_id']}.json"
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"저장 완료: {file_name}")


if __name__ == "__main__":
    main()
