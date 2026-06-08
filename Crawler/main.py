# 크롤러 진입점
# 흐름: trace_id 생성 -> (.env의 CRAWL_TARGET으로 선택된 컬렉션) x 식품 카테고리 순회
#       -> 카테고리별 상품 목록 파싱 -> 상품마다 상세페이지 수집 -> 완성되는 즉시 Kafka로 전송
#
# 상품을 모았다가 끝에 한번에 보내지 않고 "완성되는 즉시 전송"하는 이유:
#   크롤러가 중간에 멈춰도 이미 보낸 상품은 안전하게 적재되고, MongoDB 적재는
#   product_id 기준 upsert라 재실행 시 같은 상품을 다시 만나도 안전하다
#   (멱등성으로 재개 문제를 해결 - 별도의 진행상황 추적 파일이 필요 없다)
import asyncio
import os
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

import kafka_producer
from logger import get_logger
from pages import COLLECTIONS, FOOD_CATEGORIES, build_url
from parsers import kurly, kurly_detail

# 로컬 개발 중에는 .env 파일에서, k8s에서는 ConfigMap/Secret으로 주입된 환경변수를 그대로 사용한다
load_dotenv()

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# 베스트("best") / 할인("sales") 중 어떤 컬렉션을 수집할지 환경변수로 선택한다
CRAWL_TARGET = os.environ.get("CRAWL_TARGET", "best")


async def crawl_category_list(page, logger, label: str, category_name: str, url: str) -> list[dict]:
    """카테고리 페이지에서 상품 목록(카드 정보)만 수집한다."""
    logger.info(f"목록 수집 시작 - {label}/{category_name} ({url})")
    await page.goto(url, wait_until="domcontentloaded", timeout=50000)
    await page.wait_for_timeout(2000)

    # 컬리는 무한 스크롤 방식으로 상품을 지연 로딩하므로 스크롤로 콘텐츠를 더 불러와야 한다
    for _ in range(8):
        await page.mouse.wheel(0, 3000)
        await page.wait_for_timeout(1000)

    products = await kurly.parse_page(page)
    logger.info(f"목록 수집 완료 - {label}/{category_name} 상품 {len(products)}건")
    return products


async def fill_detail(page, product: dict) -> None:
    """상품 상세페이지를 방문해 상세이미지를 채운다 (실패 시 호출 측에서 처리하도록 예외를 그대로 던진다)."""
    await page.goto(product["detail_url"], wait_until="domcontentloaded", timeout=50000)
    await page.wait_for_timeout(1500)

    # 상세 설명 영역(#description)은 지연 로딩되므로 스크롤로 불러온 뒤 추출한다
    for _ in range(4):
        await page.mouse.wheel(0, 2500)
        await page.wait_for_timeout(600)

    detail = await kurly_detail.parse_detail(page)
    product["detail_blocks"] = detail["detail_blocks"]


async def process_product(page, logger, producer, trace_id: str, crawled_at: str, category_context: dict, product: dict) -> None:
    """상품 하나의 카테고리 정보를 채우고, 상세 수집까지 마친 뒤 Kafka로 전송한다.

    상세 수집에 성공하면 status="ready"(서비스에 노출 가능),
    실패하면 status="draft"(목록 정보만 적재 - 다음 크롤링에서 다시 시도됨)로 표시한다.
    """
    product.update({
        **category_context,
        "crawled_at": crawled_at,
    })

    try:
        await fill_detail(page, product)
        product["status"] = "ready"
    except Exception as e:
        logger.error(f"상세 수집 실패 - {product['name']} ({product['product_id']}): {e}")
        product["detail_blocks"] = []
        product["status"] = "draft"

    kafka_producer.send_product(producer, logger, trace_id, product)


async def run() -> None:
    trace_id = str(uuid.uuid4())
    crawled_at = datetime.now(timezone.utc).isoformat()
    logger = get_logger("crawler", trace_id)

    if CRAWL_TARGET not in COLLECTIONS:
        raise ValueError(f"알 수 없는 CRAWL_TARGET 값: {CRAWL_TARGET} (best 또는 sales만 가능)")

    label = COLLECTIONS[CRAWL_TARGET]["label"]
    logger.info(f"크롤링 작업 시작 - 대상: {label}, 카테고리 {len(FOOD_CATEGORIES)}개")

    producer = kafka_producer.create_producer()
    sent_count = 0
    # 이번 크롤링에서 확인된 product_id를 모아두었다가, 끝에 정리(sync) 메시지로 전송한다
    # -> 이번에 보이지 않은 상품은 베스트/할인 목록에서 빠진 것이므로 targets에서 제거된다
    seen_product_ids: list[str] = []

    async with Stealth().use_async(async_playwright()) as p:
        # k8s 컨테이너에는 디스플레이가 없으므로 headless로 실행한다
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=USER_AGENT, locale="ko-KR")
        page = await context.new_page()

        for category_code, category_name in FOOD_CATEGORIES.items():
            url = build_url(CRAWL_TARGET, category_code)
            try:
                products = await crawl_category_list(page, logger, label, category_name, url)
            except Exception as e:
                logger.error(f"목록 수집 실패 - {label}/{category_name}: {e}")
                continue

            category_context = {
                "target": CRAWL_TARGET,
                "label": label,
                "category_code": category_code,
                "category_name": category_name,
            }
            for product in products:
                await process_product(page, logger, producer, trace_id, crawled_at, category_context, product)
                sent_count += 1
                seen_product_ids.append(product["product_id"])

        await browser.close()

    kafka_producer.send_sync(producer, logger, trace_id, CRAWL_TARGET, seen_product_ids, crawled_at)
    kafka_producer.flush(producer)
    logger.info(f"크롤링 작업 종료 - 총 {sent_count}건 전송 (정리 대상 {len(seen_product_ids)}건)")


def main():
    asyncio.run(run())


if __name__ == "__main__":
    main()
