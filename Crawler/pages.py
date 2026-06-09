# 마켓컬리(Kurly) 크롤링 대상 설정
# - COLLECTIONS: 베스트/할인 컬렉션의 기본 URL (둘 중 하나를 환경변수 CRAWL_TARGET으로 선택)
# - FOOD_CATEGORIES: 프론트 메뉴로 노출할 식품 카테고리 - 컬렉션 URL에
#   `filters=category:{코드}`를 붙이면 해당 카테고리로 좁혀서 수집할 수 있다

COLLECTIONS = {
    "best": {
        "label": "베스트",
        "base_url": "https://www.kurly.com/collection-groups/market-best?site=MARKET&page=1&collection=market-best-logic",
    },
    "sales": {
        "label": "할인",
        "base_url": "https://www.kurly.com/collection-groups/market-sales-group?site=MARKET&page=1&collection=market-sales-main1",
    },
}

# 프론트 메뉴로 노출할 식품 카테고리 (전체 30개 중 식품 15개)
FOOD_CATEGORIES = {
    "907": "채소",
    "908": "과일·견과·쌀",
    "909": "수산·해산·건어물",
    "910": "정육·가공육·달걀",
    "911": "국·반찬·메인요리",
    "912": "간편식·밀키트·샐러드",
    "913": "면·양념·오일",
    "914": "생수·음료",
    "383": "커피·차",
    "249": "간식·과자·떡",
    "915": "베이커리",
    "018": "유제품",
    "032": "건강식품",
    "722": "와인·위스키·데낄라",
    "251": "전통주",
}

# 세일 페이지에는 전통주(251) 카테고리가 없음 — 없는 카테고리로 필터링하면 무시되어
# 엉뚱한 상품이 전통주 레이블로 저장되는 오염이 발생한다
SALES_FOOD_CATEGORIES = {k: v for k, v in FOOD_CATEGORIES.items() if k != "251"}


def build_url(target: str, category_code: str) -> str:
    """선택된 컬렉션(베스트/할인) 기본 URL에 카테고리 필터를 붙여 URL을 만든다."""
    return f"{COLLECTIONS[target]['base_url']}&filters=category:{category_code}"
