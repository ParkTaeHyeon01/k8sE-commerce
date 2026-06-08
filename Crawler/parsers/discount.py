# 할인상품(/n/superdeal) 파서
# 항목 구조: 할인율 | 판매가 | 상품명 | 배송정보 (인기상품과 달리 순위 없음)
import re

# 상품 카드 컨테이너 (지연 로딩되므로 크롤러 쪽에서 스크롤 후 호출해야 한다)
ITEM_SELECTOR = "div.box__information"

_PRICE_PATTERN = re.compile(r"^[\d,]+원$")
_PERCENT_PATTERN = re.compile(r"^\d{1,2}%$")
_SKIP_LINES = {"할인율"}

_DISCOUNT_PRICE_PATTERN = re.compile(r"할인율\s*(\d{1,2})%\s*([\d,]+)원")


async def extract_raw_items(page) -> list[str]:
    """페이지에서 후보 항목들의 원본 텍스트 목록을 가져온다."""
    locator = page.locator(ITEM_SELECTOR)
    count = await locator.count()
    return [await locator.nth(i).inner_text() for i in range(count)]


def parse_item(raw_text: str) -> dict | None:
    """항목 텍스트 하나를 파싱한다. 할인율/가격이 없으면 상품 카드가 아니므로 None을 반환한다."""
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    if not lines:
        return None

    full_text = " ".join(lines)

    price_match = _DISCOUNT_PRICE_PATTERN.search(full_text)
    if not price_match:
        return None

    name = None
    for line in lines:
        if line in _SKIP_LINES or _PRICE_PATTERN.match(line) or _PERCENT_PATTERN.match(line):
            continue
        name = line
        break

    if "무료배송" in full_text:
        delivery_info = "무료배송"
    elif "배송비" in full_text:
        delivery_info = "유료배송"
    else:
        delivery_info = None

    return {
        "name": name,
        "sale_price": int(price_match.group(2).replace(",", "")),
        "discount_rate": int(price_match.group(1)),
        "delivery_info": delivery_info,
    }


async def parse_page(page) -> list[dict]:
    """현재 페이지에서 할인상품 목록을 추출해 파싱한다 (지연 로딩이라 호출 전 스크롤 필요)."""
    raw_items = await extract_raw_items(page)
    parsed = (parse_item(raw) for raw in raw_items)
    return [item for item in parsed if item and item["name"]]
