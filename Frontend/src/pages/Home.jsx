import { useNavigate } from "react-router-dom";

const CATEGORIES = [
  { icon: "🥦", name: "채소",             code: "907" },
  { icon: "🍎", name: "과일·견과·쌀",     code: "908" },
  { icon: "🐟", name: "수산·해산·건어물", code: "909" },
  { icon: "🥩", name: "정육·가공육·달걀", code: "910" },
  { icon: "🥘", name: "국·반찬·메인요리", code: "911" },
  { icon: "🍱", name: "간편식·밀키트",    code: "912" },
  { icon: "🍜", name: "면·양념·오일",     code: "913" },
  { icon: "🧃", name: "생수·음료",        code: "914" },
  { icon: "☕", name: "커피·차",          code: "383" },
  { icon: "🍪", name: "간식·과자·떡",    code: "249" },
  { icon: "🍞", name: "베이커리",         code: "915" },
  { icon: "🧀", name: "유제품",           code: "018" },
  { icon: "🥗", name: "건강식품",         code: "032" },
  { icon: "🍷", name: "와인·위스키",      code: "722" },
  { icon: "🍶", name: "전통주",           code: "251" },
];

export default function Home() {
  const navigate = useNavigate();

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
            {CATEGORIES.map((c) => (
              <div
                key={c.name}
                className="category-card"
                onClick={() => navigate(`/products?category=${c.code}`)}
              >
                <div className="category-icon-wrap">
                  <span className="category-icon">{c.icon}</span>
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
