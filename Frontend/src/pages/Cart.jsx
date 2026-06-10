import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getCart, updateCart, removeFromCart } from "../api";
import { isLoggedIn } from "../auth";

export default function Cart() {
  const navigate = useNavigate();
  const [cart, setCart]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!isLoggedIn()) { navigate("/login"); return; }
    loadCart();
  }, []);

  const loadCart = () => {
    getCart()
      .then(setCart)
      .catch(() => setMessage("장바구니를 불러오지 못했습니다."))
      .finally(() => setLoading(false));
  };

  const handleUpdate = async (product_id, quantity) => {
    await updateCart(product_id, quantity);
    loadCart();
  };

  const handleRemove = async (product_id) => {
    await removeFromCart(product_id);
    loadCart();
  };

  if (loading) return <p className="status-msg">불러오는 중...</p>;

  const items = cart?.items ?? [];

  return (
    <div className="cart-page">
      <h2>장바구니</h2>
      {message && <p className="cart-message">{message}</p>}

      {items.length === 0 ? (
        <div className="cart-empty">
          <p>장바구니가 비어 있습니다.</p>
          <button className="btn-primary" onClick={() => navigate("/products")}>상품 보러가기</button>
        </div>
      ) : (
        <>
          <div className="cart-items">
            {items.map(item => (
              <div key={item.product_id} className="cart-item">
                <img src={item.image_url} alt={item.name} onClick={() => navigate(`/products/${item.product_id}`)} />
                <div className="cart-item-info">
                  <p className="cart-item-name" onClick={() => navigate(`/products/${item.product_id}`)}>{item.name}</p>
                  <p className="cart-item-price">{item.sale_price?.toLocaleString()}원</p>
                  {item.stock === 0 && <span className="badge-soldout">품절</span>}
                </div>
                <div className="cart-item-qty">
                  <button onClick={() => handleUpdate(item.product_id, item.quantity - 1)} disabled={item.quantity <= 1}>-</button>
                  <span>{item.quantity}</span>
                  <button onClick={() => handleUpdate(item.product_id, item.quantity + 1)} disabled={item.quantity >= item.stock}>+</button>
                </div>
                <p className="cart-item-total">{item.total_price?.toLocaleString()}원</p>
                <button className="cart-remove-btn" onClick={() => handleRemove(item.product_id)}>✕</button>
              </div>
            ))}
          </div>

          <div className="cart-summary">
            <div className="cart-total">
              총 결제 금액: <strong>{cart?.total?.toLocaleString()}원</strong>
            </div>
            <button
              className="btn-checkout"
              onClick={() => navigate("/checkout")}
              disabled={items.some(i => i.stock === 0)}
            >
              주문하기
            </button>
          </div>
        </>
      )}
    </div>
  );
}
