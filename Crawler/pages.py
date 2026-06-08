# 마켓컬리(Kurly) 크롤링 대상 페이지 설정
# 컬리는 G마켓처럼 카테고리 코드를 조합해 URL을 만드는 구조가 아니라
# "컬렉션" 단위로 고정된 URL을 그대로 사용하므로 URL을 직접 명시한다.

PAGES = {
    "market_best": {
        "label": "베스트",
        "url": "https://www.kurly.com/collection-groups/market-best?site=MARKET&page=1&collection=market-best-logic",
    },
    "market_sales": {
        "label": "할인",
        "url": "https://www.kurly.com/collection-groups/market-sales-group?site=MARKET&page=1&collection=market-sales-main1",
    },
}
