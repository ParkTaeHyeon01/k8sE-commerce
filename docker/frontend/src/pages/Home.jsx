import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { fetchCategories } from "../api";

// 카테고리 코드별 아이콘 — API에서 이름은 받아오고 아이콘은 여기서 매핑
const ICON_MAP = {
  "907": "🥦", "908": "🍎", "909": "🐟", "910": "🥩",
  "911": "🥘", "912": "🍱", "913": "🍜", "914": "🧃",
  "383": "☕", "249": "🍪", "915": "🍞", "018": "🧀",
  "032": "🥗", "722": "🍷", "251": "🍶",
};
const DEFAULT_ICON = "🛒";

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

export default function Home() {
  const navigate = useNavigate();
  const [categories, setCategories] = useState(FALLBACK_CATEGORIES);

  useEffect(() => {
    fetchCategories("best")
      .then((data) => {
        const cats = data.categories ?? [];
        if (cats.length > 0) setCategories(cats);
      })
      .catch(() => {}); // 실패 시 폴백 유지
  }, []);

  return (
    <div className="home">
      {/* 히어로 섹션 */}
      <section className="hero">
        <div className="hero-inner">
          <p className="hero-sub">신선하고 건강한 식품을 빠르게</p>
          <h1 className="hero-title">오늘의 신선함을<br />바로 만나보세요</h1>
          <div className="hero-btns">
            <button className="hero-btn-primary" onClick={() => navigate("/products")}>
              전체 상품 보기
            </button>
            <button className="hero-btn-primary" onClick={() => navigate("/products?target=best")}>
              🏆 베스트 상품 보기
            </button>
            <button className="hero-btn-secondary" onClick={() => navigate("/products?target=sales")}>
              🔥 할인 상품 보기
            </button>
          </div>
        </div>
      </section>

      {/* 카테고리 바로가기 */}
      <section className="home-section cat-section">
        <div className="home-container">
          <div className="section-header">
            <h2 className="section-title">카테고리</h2>
            <button className="section-more" onClick={() => navigate("/products")}>전체 상품 보기 →</button>
          </div>
          <div className="category-grid">
            {categories.map((c) => (
              <div
                key={c.code}
                className="category-card"
                onClick={() => navigate(`/products?category=${c.code}`)}
              >
                <div className="category-icon-wrap">
                  <span className="category-icon">{ICON_MAP[c.code] ?? DEFAULT_ICON}</span>
                </div>
                <span className="category-name">{c.name}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 기획전 배너 */}
      <section className="home-section">
        <div className="home-container">
          <div className="banner-row">
            <div className="banner banner-best" onClick={() => navigate("/products?target=best")}>
              <p className="banner-label">BEST</p>
              <h3>지금 가장 인기있는<br />베스트 상품</h3>
              <span className="banner-link">바로가기 →</span>
            </div>
            <div className="banner banner-sales" onClick={() => navigate("/products?target=sales")}>
              <p className="banner-label">SALE</p>
              <h3>최대 할인 중인<br />특가 상품</h3>
              <span className="banner-link">바로가기 →</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
