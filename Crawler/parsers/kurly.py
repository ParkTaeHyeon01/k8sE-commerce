# 마켓컬리 상품 카드 파서 (베스트/할인 페이지 공통 - 카드 구조가 동일하다)
# 카드 구조: (쿠폰/혜택 뱃지) | 담기 버튼 | 배송유형 | 상품명 | 한줄설명 | 가격 정보 | 재고 | (Kurly Only)
# 가격 정보는 할인이 있으면 "정가 -> 할인율 -> 할인가" 3줄, 없으면 가격 1줄만 나온다
import re

# 상품 카드 컨테이너 (지연 로딩이라 크롤러 쪽에서 스크롤 후 호출해야 한다)
ITEM_SELECTOR = "article"

_CART_BUTTON = "담기"
_PRICE_PATTERN = re.compile(r"^([\d,]+)원~?$")
_PERCENT_PATTERN = re.compile(r"^(\d{1,3})%$")


async def extract_raw_items(page) -> list[str]:
    """페이지에서 후보 항목들의 원본 텍스트 목록을 가져온다."""
    locator = page.locator(ITEM_SELECTOR)
    count = await locator.count()
    return [await locator.nth(i).inner_text() for i in range(count)]


def parse_item(raw_text: str) -> dict | None:
    """항목 텍스트 하나를 파싱한다. '담기' 버튼이 없으면 상품 카드가 아니므로 None을 반환한다."""
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    if _CART_BUTTON not in lines:
        return None

    # '담기' 다음 줄부터가 실제 상품 정보다 (그 앞은 쿠폰/혜택 뱃지)
    rest = lines[lines.index(_CART_BUTTON) + 1:]
    if not rest:
        return None

    delivery_info = rest[0] if rest[0].endswith("배송") else None
    body = rest[1:] if delivery_info else rest
    if not body:
        return None

    name = body[0]

    prices = []
    discount_rate = None
    for line in body[1:]:
        price_match = _PRICE_PATTERN.match(line)
        if price_match:
            prices.append(int(price_match.group(1).replace(",", "")))
            continue
        percent_match = _PERCENT_PATTERN.match(line)
        if percent_match:
            discount_rate = int(percent_match.group(1))

    if len(prices) >= 2:
        original_price, sale_price = prices[0], prices[1]
    elif len(prices) == 1:
        original_price, sale_price, discount_rate = None, prices[0], None
    else:
        return None

    return {
        "name": name,
        "original_price": original_price,
        "sale_price": sale_price,
        "discount_rate": discount_rate,
        "delivery_info": delivery_info,
    }


async def parse_page(page) -> list[dict]:
    """현재 페이지에서 상품 목록을 추출해 파싱한다 (지연 로딩이라 호출 전 스크롤 필요)."""
    raw_items = await extract_raw_items(page)
    parsed = (parse_item(raw) for raw in raw_items)
    return [item for item in parsed if item and item["name"]]
