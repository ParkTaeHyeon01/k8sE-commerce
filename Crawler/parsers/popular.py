# 인기상품(/n/best) 파서
# 항목 구조: 순위 | 상품명 | 원가 | 할인율 | 판매가 | 배송정보
import re

# 상품 카드로 추정되는 li 요소 (메뉴/배너 등도 섞여 있어 parse_item에서 한 번 더 거른다)
ITEM_SELECTOR = "li[class*='item']"

_RANK_PATTERN = re.compile(r"^(\d+)$")
_PRICE_PATTERN = re.compile(r"^[\d,]+원$")
_PERCENT_PATTERN = re.compile(r"^\d{1,2}%$")
_SKIP_LINES = {"쿠폰적용가", "원가", "할인율", "판매가", "무료배송", "오늘출발"}


async def extract_raw_items(page) -> list[str]:
    """페이지에서 후보 항목들의 원본 텍스트 목록을 가져온다."""
    locator = page.locator(ITEM_SELECTOR)
    count = await locator.count()
    return [await locator.nth(i).inner_text() for i in range(count)]


def parse_item(raw_text: str) -> dict | None:
    """항목 텍스트 하나를 파싱한다. 순위로 시작하지 않으면 상품이 아니므로 None을 반환한다."""
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    if not lines:
        return None

    rank_match = _RANK_PATTERN.match(lines[0])
    if not rank_match:
        return None

    full_text = " ".join(lines)

    name = None
    for line in lines[1:]:
        if line in _SKIP_LINES or _PRICE_PATTERN.match(line) or _PERCENT_PATTERN.match(line):
            continue
        name = line
        break

    def _extract_int(pattern: str):
        m = re.search(pattern, full_text)
        return int(m.group(1).replace(",", "")) if m else None

    discount_match = re.search(r"할인율\s*(\d{1,2})%", full_text)

    return {
        "rank": int(rank_match.group(1)),
        "name": name,
        "original_price": _extract_int(r"원가\s*([\d,]+)원"),
        "sale_price": _extract_int(r"판매가\s*([\d,]+)원"),
        "discount_rate": int(discount_match.group(1)) if discount_match else None,
        "delivery_info": "무료배송" if "무료배송" in full_text else "유료배송",
    }


async def parse_page(page) -> list[dict]:
    """현재 페이지에서 인기상품 목록을 추출해 파싱한다."""
    raw_items = await extract_raw_items(page)
    parsed = (parse_item(raw) for raw in raw_items)
    return [item for item in parsed if item and item["name"]]
