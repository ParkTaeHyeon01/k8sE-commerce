# 마켓컬리 상품 상세페이지 파서
# 상세 설명 영역(#description)은 이미지와 본문 텍스트(소개/보관법/조리법 등)가
# 순서대로 섞여 있다. 원본의 "이미지-텍스트가 번갈아 나오는 구성"을 그대로
# 재현할 수 있도록, 등장 순서를 보존한 블록 배열로 추출한다.
# #description 안에는 실제 본문(.goods_wrap) 외에도 상품고시정보, 추천 상품
# 캐러셀 등이 같은 태그(h3/p)로 섞여 있어, 본문 컨테이너로 범위를 좁힌다
DESCRIPTION_SELECTOR = "#description .goods_wrap"
_BLOCK_SELECTOR = "img, h3, p.words"


async def extract_detail_blocks(page) -> list[dict]:
    """상세 설명 영역을 등장 순서대로 {type, value} 블록 배열로 추출한다.

    - 이미지: kurly.com 도메인이 아닌 것은 장식용 SVG 아이콘이므로 제외
    - 텍스트: 비어있는 경우 제외 ("상품설명 및 상품이미지 참조" 같은 placeholder는
      h3/p.words 밖에 있어 자연스럽게 걸러진다)
    """
    # 주의: "A B, C, D"는 CSS에서 (A B), C, D로 해석되어 범위를 벗어난다.
    # :is()로 묶어야 DESCRIPTION_SELECTOR 하위로 올바르게 범위가 좁혀진다.
    raw_blocks = await page.locator(f"{DESCRIPTION_SELECTOR} :is({_BLOCK_SELECTOR})").evaluate_all(
        """els => els.map(e => {
            if (e.tagName === 'IMG') {
                return {type: 'image', value: e.getAttribute('src') || e.getAttribute('data-src')};
            }
            return {type: 'text', value: e.innerText.trim()};
        })"""
    )

    blocks = []
    for block in raw_blocks:
        if block["type"] == "image":
            if block["value"] and "kurly.com" in block["value"]:
                blocks.append(block)
        elif block["value"]:
            blocks.append(block)
    return blocks


async def parse_detail(page) -> dict:
    """상세페이지에서 상세 정보를 추출한다 (호출 전 상세 영역까지 스크롤 필요)."""
    return {
        "detail_blocks": await extract_detail_blocks(page),
    }
