# 마켓컬리 상품 상세페이지 파서
# 상세페이지 본문(#description)에는 상품고시정보가 대부분
# "상품설명 및 상품이미지 참조"로 채워져 있어 텍스트 자체에는 의미가 없고,
# 실제 상세 정보는 이 영역의 이미지들 안에 들어있다 -> 이미지 URL만 수집한다
DESCRIPTION_SELECTOR = "#description img"


async def extract_detail_images(page) -> list[str]:
    """상세 설명 영역의 이미지 URL만 추출한다 (장식용 SVG 아이콘은 kurly.com 도메인이 아니므로 제외)."""
    sources = await page.locator(DESCRIPTION_SELECTOR).evaluate_all(
        "els => els.map(e => e.getAttribute('src') || e.getAttribute('data-src'))"
    )
    return [src for src in sources if src and "kurly.com" in src]


async def parse_detail(page) -> dict:
    """상세페이지에서 상세 정보를 추출한다 (호출 전 상세 영역까지 스크롤 필요)."""
    return {
        "detail_images": await extract_detail_images(page),
    }
