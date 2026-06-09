import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchProducts } from "../api";

const CATEGORIES = [
  { code: "", name: "전체" },
  { code: "907", name: "채소" },
  { code: "908", name: "과일" },
  { code: "912", name: "수산·해산물" },
  { code: "915", name: "정육·계란류" },
  { code: "921", name: "유제품·치즈" },
  { code: "924", name: "두부·콩나물·달걀" },
  { code: "925", name: "쌀·잡곡·견과" },
  { code: "906", name: "국·반찬·메인요리" },
  { code: "919", name: "면·통조림·가공식품" },
  { code: "910", name: "생수·음료·주류" },
  { code: "911", name: "건강식품" },
  { code: "920", name: "간식·과자·떡" },
  { code: "905", name: "냉동·간편식" },
  { code: "922", name: "베이커리·떡" },
  { code: "916", name: "커피·차" },
];

const PAGE_SIZE = 20;

export default function ProductList() {
  const navigate = useNavigate();
  const [target, setTarget] = useState("best");
  const [categoryCode, setCategoryCode] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchProducts({ target, category_code: categoryCode, page, page_size: PAGE_SIZE })
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [target, categoryCode, page]);

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  const handleTargetChange = (t) => {
    setTarget(t);
    setPage(1);
  };

  const handleCategoryChange = (e) => {
    setCategoryCode(e.target.value);
    setPage(1);
  };

  return (
    <>
      <div className="filter-bar">
        <div className="container">
          <button className={target === "best" ? "active" : ""} onClick={() => handleTargetChange("best")}>베스트</button>
          <button className={target === "sales" ? "active" : ""} onClick={() => handleTargetChange("sales")}>할인</button>
          <select value={categoryCode} onChange={handleCategoryChange}>
            {CATEGORIES.map((c) => (
              <option key={c.code} value={c.code}>{c.name}</option>
            ))}
          </select>
          {data && <span className="result-count">총 {data.total.toLocaleString()}개</span>}
        </div>
      </div>

      <div className="container">
        {loading && <p className="status-msg">불러오는 중...</p>}
        {error && <p className="status-msg">오류: {error}</p>}
        {!loading && !error && data && (
          <>
            <div className="product-grid">
              {data.products.map((p) => (
                <div key={p.product_id} className="product-card" onClick={() => navigate(`/products/${p.product_id}`)}>
                  <img src={p.image_url} alt={p.name} loading="lazy" />
                  <div className="card-body">
                    <p className="name">{p.name}</p>
                    <div className="price-row">
                      {p.discount_rate > 0 && <span className="discount">{p.discount_rate}%</span>}
                      <span className="sale-price">{p.sale_price?.toLocaleString()}원</span>
                    </div>
                    {p.original_price > 0 && p.original_price !== p.sale_price && (
                      <p className="original-price">{p.original_price?.toLocaleString()}원</p>
                    )}
                    {p.delivery_info && <p className="delivery">{p.delivery_info}</p>}
                  </div>
                </div>
              ))}
            </div>

            {totalPages > 1 && (
              <div className="pagination">
                <button disabled={page === 1} onClick={() => setPage((p) => p - 1)}>이전</button>
                {Array.from({ length: Math.min(totalPages, 10) }, (_, i) => {
                  const p = i + 1;
                  return (
                    <button key={p} className={page === p ? "active" : ""} onClick={() => setPage(p)}>{p}</button>
                  );
                })}
                <button disabled={page === totalPages} onClick={() => setPage((p) => p + 1)}>다음</button>
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}
