def make_ngrams(text: str, min_n: int = 2, max_n: int = 4) -> list:
    """상품명에서 n-gram 토큰 생성. 부분 문자열 검색 지원용."""
    tokens = set()
    for word in text.split():
        if not word:
            continue
        tokens.add(word)  # 단어 전체
        for n in range(min_n, min(max_n + 1, len(word) + 1)):
            for i in range(len(word) - n + 1):
                tokens.add(word[i:i+n])
    return list(tokens)
