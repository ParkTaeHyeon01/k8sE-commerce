# 마켓컬리 상품 상세페이지 파서
# "상품고시정보" 텍스트가 등장하기 직전까지의 img/텍스트 블록을 순서대로 수집한다.
# CSS 클래스 의존 없이 DOM 위치 기반으로 잘라내므로 페이지 구조 변경에 강하다.

_EXTRACT_JS = """
() => {
    const desc = document.querySelector('#description');
    if (!desc) return [];

    // "상품고시정보" 텍스트를 가진 첫 번째 요소를 기준점으로 삼는다
    let cutoff = null;
    for (const el of desc.querySelectorAll('*')) {
        if (el.childElementCount === 0 && el.textContent.trim() === '상품고시정보') {
            cutoff = el;
            break;
        }
    }

    const TEXT_TAGS = new Set(['H3', 'P', 'LI']);
    const blocks = [];
    for (const el of desc.querySelectorAll('img, h3, p, li')) {
        // cutoff 이후(DOCUMENT_POSITION_FOLLOWING=4)이면 수집 중단
        if (cutoff && (cutoff.compareDocumentPosition(el) & 4) === 0) break;

        // 텍스트 요소가 같은 종류의 조상 안에 중첩된 경우 중복 방지
        if (TEXT_TAGS.has(el.tagName)) {
            let ancestor = el.parentElement;
            let skip = false;
            while (ancestor && ancestor !== desc) {
                if (TEXT_TAGS.has(ancestor.tagName)) { skip = true; break; }
                ancestor = ancestor.parentElement;
            }
            if (skip) continue;
        }

        if (el.tagName === 'IMG') {
            // lazy load 속성을 순서대로 시도
            const src = el.src
                || el.getAttribute('data-src')
                || el.getAttribute('data-lazy-src')
                || el.getAttribute('data-original')
                || '';
            if (src && !src.startsWith('data:') && !src.startsWith('blob:')) {
                blocks.push({type: 'image', value: src});
            }
        } else {
            const text = el.innerText.trim();
            // 짧은 UI 레이블(버튼 텍스트 등)은 제외
            if (text && text.length > 1) {
                blocks.push({type: 'text', value: text});
            }
        }
    }
    return blocks;
}
"""


async def parse_detail(page) -> dict:
    """#description 내에서 상품고시정보 이전까지의 블록을 추출한다."""
    blocks = await page.evaluate(_EXTRACT_JS)
    return {"detail_blocks": blocks}
