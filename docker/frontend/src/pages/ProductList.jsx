import { useEffect, useState, useRef, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { fetchCategories, fetchProducts, addToCart, fetchSuggest } from "../api";
import { isLoggedIn } from "../auth";

const TABS = [
  { value: "", label: "전체" },
  { value: "best", label: "베스트" },
  { value: "sales", label: "할인" },
];

const SORT_OPTIONS = [
  { value: "rank", label: "인기순" },
  { value: "price_asc", label: "낮은 가격순" },
  { value: "price_desc", label: "높은 가격순" },
  { value: "discount_desc", label: "할인율 높은순" },
];

const FALLBACK_CATEGORIES = [
  { code: "251", name: "전통주" },
  { code: "907", name: "채소" }, { code: "908", name: "과일·견과·쌀" },
  { code: "909", name: "수산·해산·건어물" }, { code: "910", name: "정육·가공육·달걀" },
  { code: "911", name: "국·반찬·메인요리" }, { code: "912", name: "간편식·밀키트·샐러드" },
  { code: "913", name: "면·양념·오일" }, { code: "914", name: "생수·음료" },
  { code: "383", name: "커피·차" }, { code: "249", name: "간식·과자·떡" },
  { code: "915", name: "베이커리" }, { code: "018", name: "유제품" },
  { code: "032", name: "건강식품" }, { code: "722", name: "와인·위스키·데낄라" },
];

const PAGE_SIZE = 20;

export default function ProductList() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [target, setTarget]             = useState(searchParams.get("target") || "");
  const [categoryCode, setCategoryCode] = useState(searchParams.get("category") || "");
  const [sortBy, setSortBy]             = useState("rank");
  const [page, setPage]                 = useState(1);
  const [refreshKey, setRefreshKey]     = useState(0);
  const [data, setData]                 = useState(null);
  const [loading, setLoading]           = useState(false);
  const [error, setError]               = useState(null);
  const [categories, setCategories]     = useState(FALLBACK_CATEGORIES);
  const [cartMsg, setCartMsg]           = useState("");

  // 검색
  const [searchInput, setSearchInput]   = useState("");
  const [activeQuery, setActiveQuery]   = useState("");
  const [suggestions, setSuggestions]   = useState([]);
  const [showSuggest, setShowSuggest]   = useState(false);
  const debounceRef = useRef(null);
  const searchRef   = useRef(null);

  useEffect(() => {
    fetchCategories(target)
      .then((d) => { if ((d.categories ?? []).length > 0) setCategories(d.categories); })
      .catch(() => {});
  }, [target]);

  useEffect(() => {
    setLoading(true); setError(null); setData(null);
    fetchProducts({ target, category_code: categoryCode, page, page_size: PAGE_SIZE, sort_by: sortBy, q: activeQuery })
      .then(setData).catch((e) => setError(e.message)).finally(() => setLoading(false));
  }, [target, categoryCode, sortBy, page, refreshKey, activeQuery]);

  // 검색창 외부 클릭 시 드롭다운 닫기
  useEffect(() => {
    const onClickOutside = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setShowSuggest(false);
      }
    };
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  const handleSearchInput = useCallback((e) => {
    const val = e.target.value;
    setSearchInput(val);
    clearTimeout(debounceRef.current);
    if (!val.trim()) { setSuggestions([]); setShowSuggest(false); return; }
    debounceRef.current = setTimeout(async () => {
      const res = await fetchSuggest(val.trim());
      const list = res.suggestions ?? [];
      setSuggestions(list);
      setShowSuggest(list.length > 0);
    }, 200);
  }, []);

  const submitSearch = (q) => {
    setActiveQuery(q);
    setPage(1);
    setShowSuggest(false);
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    submitSearch(searchInput.trim());
  };

  const handleSuggestClick = (word) => {
    setSearchInput(word);
    submitSearch(word);
  };

  const handleClearSearch = () => {
    setSearchInput("");
    setActiveQuery("");
    setSuggestions([]);
    setShowSuggest(false);
    setPage(1);
  };

  const totalPages = data ? Math.ceil((data.total ?? 0) / PAGE_SIZE) : 0;

  const handleTabChange = (t) => {
    setSearchInput(""); setActiveQuery(""); setSuggestions([]); setShowSuggest(false);
    if (t === target) { setCategoryCode(""); setSortBy("rank"); setPage(1); setRefreshKey(k => k + 1); }
    else { setTarget(t); setCategoryCode(""); setSortBy("rank"); setPage(1); }
  };

  const handleAddToCart = async (e, product_id, goToCart) => {
    e.stopPropagation();
    if (!isLoggedIn()) { navigate("/login"); return; }
    try {
      await addToCart(product_id, 1);
      window.dispatchEvent(new Event("cart-change"));
      if (goToCart) {
        navigate("/cart");
      } else {
        setCartMsg("장바구니에 담았습니다.");
        setTimeout(() => setCartMsg(""), 2000);
      }
    } catch (err) {
      setCartMsg(err.message);
      setTimeout(() => setCartMsg(""), 2000);
    }
  };

  return (
    <>
      <nav className="top-nav">
        <div className="top-nav-inner">
          {TABS.map((t) => (
            <button key={t.value} className={`nav-tab ${target === t.value ? "active" : ""}`} onClick={() => handleTabChange(t.value)}>
              {t.label}
            </button>
          ))}
        </div>
      </nav>

      {cartMsg && <div className="cart-toast">{cartMsg}</div>}

      <div className="page-layout">
        <aside className="sidebar">
          <div className="sidebar-title">카테고리</div>
          <ul className="sidebar-list">
            {categories.map((c) => (
              <li key={c.code}>
                <button className={`sidebar-item ${categoryCode === c.code ? "active" : ""}`} onClick={() => { setCategoryCode(prev => prev === c.code ? "" : c.code); setPage(1); }}>
                  {c.name}
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <main className="main-content">
          {/* 검색바 */}
          <div className="product-search-wrap" ref={searchRef}>
            <form className="product-search-form" onSubmit={handleSearchSubmit}>
              <input
                className="product-search-input"
                type="text"
                placeholder="상품명 검색..."
                value={searchInput}
                onChange={handleSearchInput}
                onFocus={() => suggestions.length > 0 && setShowSuggest(true)}
              />
              {searchInput && (
                <button type="button" className="product-search-clear" onClick={handleClearSearch}>✕</button>
              )}
              <button type="submit" className="product-search-btn">검색</button>
            </form>
            {showSuggest && (
              <ul className="suggest-list">
                {suggestions.map((s) => (
                  <li key={s} className="suggest-item" onMouseDown={() => handleSuggestClick(s)}>
                    {s}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="result-bar">
            <span className="result-count">
              {data ? (
                activeQuery
                  ? <><b>"{activeQuery}"</b> 검색 결과 <b>{(data.total ?? 0).toLocaleString()}</b>개</>
                  : <>총 <b>{(data.total ?? 0).toLocaleString()}</b>개</>
              ) : ""}
            </span>
            <select className="sort-select" value={sortBy} onChange={(e) => { setSortBy(e.target.value); setPage(1); }}>
              {SORT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          {loading && <p className="status-msg">불러오는 중...</p>}
          {error   && <p className="status-msg">오류: {error}</p>}
          {!loading && !error && data && (data.products ?? []).length === 0 && (
            <p className="empty-msg">
              {activeQuery ? `"${activeQuery}"에 대한 검색 결과가 없습니다.` : "상품이 없습니다.\n크롤링 후 다시 확인해주세요."}
            </p>
          )}

          {!loading && !error && data && (data.products ?? []).length > 0 && (
            <>
              <div className="product-grid">
                {(data.products ?? []).map((p) => (
                  <div key={p.product_id} className={`product-card ${p.stock === 0 ? "soldout" : ""}`} onClick={() => navigate(`/products/${p.product_id}`)}>
                    <div className="card-img-wrap">
                      <img src={p.image_url} alt={p.name} loading="lazy" />
                      {p.discount_rate > 0 && <span className="badge-discount">{p.discount_rate}%</span>}
                      {p.stock === 0 && <span className="badge-soldout-overlay">품절</span>}
                    </div>
                    <div className="card-body">
                      <p className="cat-label">{p.category_name}</p>
                      <p className="name">{p.name}</p>
                      <div className="price-row">
                        <span className="sale-price">{p.sale_price?.toLocaleString()}원</span>
                        {p.original_price > 0 && p.original_price !== p.sale_price && (
                          <span className="original-price">{p.original_price?.toLocaleString()}원</span>
                        )}
                      </div>
                      {p.delivery_info && <p className="delivery-info">{p.delivery_info}</p>}
                      <p className="stock-info">{p.stock > 0 ? `재고 ${p.stock}개` : "품절"}</p>
                    </div>
                    <div className="card-actions" onClick={e => e.stopPropagation()}>
                      {p.stock > 0 && <>
                        <button className="btn-cart-add"  onClick={e => handleAddToCart(e, p.product_id, false)}>장바구니</button>
                        <button className="btn-buy"       onClick={e => handleAddToCart(e, p.product_id, true)}>구매</button>
                      </>}
                    </div>
                  </div>
                ))}
              </div>

              {totalPages > 1 && (
                <div className="pagination">
                  <button className="pg-arrow" disabled={page === 1} onClick={() => setPage(p => p - 1)}>← 이전</button>
                  {Array.from({ length: Math.min(totalPages, 10) }, (_, i) => i + 1).map((p) => (
                    <button key={p} className={page === p ? "active" : ""} onClick={() => setPage(p)}>{p}</button>
                  ))}
                  <button className="pg-arrow" disabled={page === totalPages} onClick={() => setPage(p => p + 1)}>다음 →</button>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </>
  );
}
