import { BrowserRouter, Route, Routes, useNavigate } from "react-router-dom";
import ProductList from "./pages/ProductList";
import ProductDetail from "./pages/ProductDetail";

function Header() {
  const navigate = useNavigate();
  return (
    <header className="header">
      <div className="container">
        <h1 onClick={() => navigate("/")}>🛒 마켓컬리 베스트/할인</h1>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Header />
      <Routes>
        <Route path="/" element={<ProductList />} />
        <Route path="/products/:product_id" element={<ProductDetail />} />
      </Routes>
    </BrowserRouter>
  );
}
