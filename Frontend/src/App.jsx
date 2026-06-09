import { BrowserRouter, Route, Routes, useNavigate } from "react-router-dom";
import Home from "./pages/Home";
import ProductList from "./pages/ProductList";
import ProductDetail from "./pages/ProductDetail";

function Header() {
  const navigate = useNavigate();
  return (
    <header className="header">
      <div className="header-inner">
        <div className="header-logo" onClick={() => navigate("/")}>
          <div className="logo-text">식품 <span>이커머스</span></div>
        </div>
        <div className="header-auth">
          <button className="btn-login">로그인</button>
          <button className="btn-signup">회원가입</button>
        </div>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Header />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/products" element={<ProductList />} />
        <Route path="/products/:product_id" element={<ProductDetail />} />
      </Routes>
    </BrowserRouter>
  );
}
