import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { fetchCategories, fetchProducts } from "../api";

const TABS = [
  { value: "", label: "전체" },
  { value: "best", label: "베스트" },
  { value: "sales", label: "할인" },
];

const SORT_OPTIONS = [
  { value: "", label: "기본순" },
  { value: "rank", label: "인기순" },
  { value: "price_asc", label: "낮은 가격순" },
  { value: "price_desc", label: "높은 가격순" },
  { value: "discount_desc", label: "할인율 높은순" },
];

// API 실패 시 표시할 폴백 목록
const FALLBACK_CATEGORIES = [
  { code: "907", name: "채소" }, { code: "908", name: "과일·견과·쌀" },
  { code: "909", name: "수산·해산·건어물" }, { code: "910", name: "정육·가공육·달걀" },
  { code: "911", name: "국·반찬·메인요리" }, { code: "912", name: "간편식·밀키트·샐러드" },
  { code: "913", name: "면·양념·오일" }, { code: "914", name: "생수·음료" },
  { code: "383", name: "커피·차" }, { code: "249", name: "간식·과자·떡" },
  { code: "915", name: "베이커리" }, { code: "018", name: "유제품" },
  { code: "032", name: "건강식품" }, { code: "722", name: "와인·위스키·데낄라" },
  { code: "251", name: "전통주" },
];

const PAGE_SIZE = 20;

export default function ProductList() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [target, setTarget] = useState(searchParams.get("target") || "");
  const [categoryCode, setCategoryCode] = useState(searchParams.get("category") || "");
  const [sortBy, setSortBy] = useState("");
  const [page, setPage] = useState(1);
  const [refreshKey, setRefreshKey] = useState(0);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [categories, setCategories] = useState(FALLBACK_CATEGORIES);

  // target이 바뀌면 해당 target의 카테고리 목록을 다시 불러온다
  useEffect(() => {
    fetchCategories(target)
      .then((data) => {
        const cats = data.categories ?? [];
        if (cats.length > 0) setCategories(cats);
      })
      .catch(() => {}); // 실패 시 폴백 유지
  }, [target]);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setData(null);
    fetchProducts({ target, category_code: categoryCode, page, page_size: PAGE_SIZE, sort_by: sortBy })
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [target, categoryCode, sortBy, page, refreshKey]);

  const totalPages = data ? Math.ceil((data.total ?? 0) / PAGE_SIZE) : 0;

  const handleTabChange = (t) => {
    if (t === target) {
      setCategoryCode("");
      setSortBy("");
      setPage(1);
      setRefreshKey(k => k + 1);
    } else {
      setTarget(t);
      setCategoryCode("");
      // 전체 탭으로 이동 시 인기순이 선택돼 있었다면 기본순으로 초기화
      setSortBy(prev => (t === "" && prev === "rank") ? "" : prev);
      setPage(1);
    }
  };

  const handleCatChange = (code) => {
    setCategoryCode(prev => prev === code ? "" : code);
    setPage(1);
  };

  return (
    <>
      {/* 중앙 탭 네비 */}
      <nav className="top-nav">
        <div className="top-nav-inner">
          {TABS.map((t) => (
            <button
              key={t.value}
              className={`nav-tab ${target === t.value ? "active" : ""}`}
              onClick={() => handleTabChange(t.value)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </nav>

      {/* 사이드바 + 상품 영역 */}
      <div className="page-layout">
        {/* 사이드바 */}
        <aside className="sidebar">
          <div className="sidebar-title">카테고리</div>
          <ul className="sidebar-list">
            {categories.map((c) => (
              <li key={c.code}>
                <button
                  className={`sidebar-item ${categoryCode === c.code ? "active" : ""}`}
                  onClick={() => handleCatChange(c.code)}
                >
                  {c.name}
                </button>
              </li>
            ))}
          </ul>
        </aside>

        {/* 상품 메인 */}
        <main className="main-content">
          <div className="result-bar">
            <span className="result-count">
              {data ? <>총 <b>{(data.total ?? 0).toLocaleString()}</b>개</> : ""}
            </span>
            <select
              className="sort-select"
              value={sortBy}
              onChange={(e) => { setSortBy(e.target.value); setPage(1); }}
            >
              {SORT_OPTIONS.filter((o) => o.value !== "rank" || target !== "").map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          {loading && <p className="status-msg">불러오는 중...</p>}
          {error && <p className="status-msg">오류: {error}</p>}
          {!loading && !error && data && (data.products ?? []).length === 0 && (
            <p className="empty-msg">상품이 없습니다.<br />크롤링 후 다시 확인해주세요.</p>
          )}

          {!loading && !error && data && (data.products ?? []).length > 0 && (
            <>
              <div className="product-grid">
                {(data.products ?? []).map((p) => (
                  <div key={p.product_id} className="product-card" onClick={() => navigate(`/products/${p.product_id}`)}>
                    <div className="card-img-wrap">
                      <img src={p.image_url} alt={p.name} loading="lazy" />
                      {p.discount_rate > 0 && (
                        <span className="badge-discount">{p.discount_rate}%</span>
                      )}
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
                    </div>
                  </div>
                ))}
              </div>

              {totalPages > 1 && (
                <div className="pagination">
                  <button className="pg-arrow" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>← 이전</button>
                  {Array.from({ length: Math.min(totalPages, 10) }, (_, i) => i + 1).map((p) => (
                    <button key={p} className={page === p ? "active" : ""} onClick={() => setPage(p)}>{p}</button>
                  ))}
                  <button className="pg-arrow" disabled={page === totalPages} onClick={() => setPage((p) => p + 1)}>다음 →</button>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </>
  );
}
