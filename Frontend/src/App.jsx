import { BrowserRouter, Route, Routes, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import Home from "./pages/Home";
import ProductList from "./pages/ProductList";
import ProductDetail from "./pages/ProductDetail";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Cart from "./pages/Cart";
import Checkout from "./pages/Checkout";
import MyPage from "./pages/MyPage";
import Admin from "./pages/Admin";
import { getUser, removeToken } from "./auth";
import { getCart } from "./api";

function Header() {
  const navigate = useNavigate();
  const [user, setUser]         = useState(getUser());
  const [cartCount, setCartCount] = useState(0);

  useEffect(() => {
    setUser(getUser());
    if (getUser()) {
      getCart().then(data => setCartCount(data.items?.length ?? 0)).catch(() => {});
    }
  }, []);

  // 라우트 변경 시 유저/장바구니 갱신
  useEffect(() => {
    const onStorage = () => setUser(getUser());
    window.addEventListener("storage", onStorage);
    window.addEventListener("auth-change", () => {
      const u = getUser();
      setUser(u);
      if (u) {
        getCart().then(data => setCartCount(data.items?.length ?? 0)).catch(() => {});
      } else {
        setCartCount(0);
      }
    });
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const handleLogout = () => {
    removeToken();
    setUser(null);
    setCartCount(0);
    navigate("/");
  };

  return (
    <header className="header">
      <div className="header-inner">
        <div className="header-logo" onClick={() => navigate("/")}>
          <div className="logo-text">식품 <span>이커머스</span></div>
        </div>
        <div className="header-auth">
          {user ? (
            <>
              {user.is_admin && (
                <button className="btn-admin" onClick={() => navigate("/admin")}>관리자</button>
              )}
              <button className="btn-cart" onClick={() => navigate("/cart")}>
                장바구니{cartCount > 0 && <span className="cart-badge">{cartCount}</span>}
              </button>
              <button className="btn-mypage" onClick={() => navigate("/me")}>마이페이지</button>
              <button className="btn-logout" onClick={handleLogout}>로그아웃</button>
            </>
          ) : (
            <>
              <button className="btn-login" onClick={() => navigate("/login")}>로그인</button>
              <button className="btn-signup" onClick={() => navigate("/register")}>회원가입</button>
            </>
          )}
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
        <Route path="/"                    element={<Home />} />
        <Route path="/products"            element={<ProductList />} />
        <Route path="/products/:product_id" element={<ProductDetail />} />
        <Route path="/login"               element={<Login />} />
        <Route path="/register"            element={<Register />} />
        <Route path="/cart"                element={<Cart />} />
        <Route path="/checkout"            element={<Checkout />} />
        <Route path="/me"                  element={<MyPage />} />
        <Route path="/admin"               element={<Admin />} />
      </Routes>
    </BrowserRouter>
  );
}
