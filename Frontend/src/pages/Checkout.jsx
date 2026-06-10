import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getCart, getAddresses, addAddress, checkout, getMyPoints } from "../api";
import { isLoggedIn } from "../auth";

export default function Checkout() {
  const navigate = useNavigate();

  const [cart, setCart]           = useState(null);
  const [points, setPoints]       = useState(0);
  const [addresses, setAddresses] = useState([]);
  const [selectedAddr, setSelectedAddr] = useState(null);

  const [showAddForm, setShowAddForm]   = useState(false);
  const [addrForm, setAddrForm]         = useState({ recipient: "", phone: "", zipcode: "", address: "", address_detail: "" });

  const [loading, setLoading]   = useState(true);
  const [paying, setPaying]     = useState(false);
  const [error, setError]       = useState("");

  useEffect(() => {
    if (!isLoggedIn()) { navigate("/login"); return; }
    Promise.all([getCart(), getAddresses(), getMyPoints()])
      .then(([cartData, addrData, ptData]) => {
        setCart(cartData);
        const addrs = addrData.addresses ?? [];
        setAddresses(addrs);
        // 기본 배송지 자동 선택
        const def = addrs.find(a => a.is_default) ?? addrs[0] ?? null;
        setSelectedAddr(def?.id ?? null);
        setPoints(ptData.points ?? 0);
      })
      .catch(() => setError("정보를 불러오지 못했습니다."))
      .finally(() => setLoading(false));
  }, []);

  // 카카오 주소 검색 팝업
  const openPostcode = () => {
    if (!window.daum?.Postcode) {
      alert("주소 검색 스크립트를 불러오지 못했습니다.");
      return;
    }
    new window.daum.Postcode({
      oncomplete(data) {
        setAddrForm(f => ({
          ...f,
          zipcode: data.zonecode,
          address: data.roadAddress || data.jibunAddress,
        }));
      },
    }).open();
  };

  const handleAddAddress = async (e) => {
    e.preventDefault();
    if (!addrForm.recipient || !addrForm.phone || !addrForm.zipcode || !addrForm.address) {
      setError("필수 항목을 모두 입력해주세요.");
      return;
    }
    try {
      const res = await addAddress({
        recipient:      addrForm.recipient,
        phone:          addrForm.phone,
        zipcode:        addrForm.zipcode,
        address:        addrForm.address,
        address_detail: addrForm.address_detail,
      });
      // 목록 갱신 후 새로 추가된 주소 선택
      const addrData = await getAddresses();
      const addrs = addrData.addresses ?? [];
      setAddresses(addrs);
      setSelectedAddr(res.address_id);
      setShowAddForm(false);
      setAddrForm({ recipient: "", phone: "", zipcode: "", address: "", address_detail: "" });
      setError("");
    } catch (err) {
      setError(err.message);
    }
  };

  const handleCheckout = async () => {
    if (!selectedAddr) {
      setError("배송지를 선택해주세요.");
      return;
    }
    if ((cart?.total ?? 0) > points) {
      setError("포인트가 부족합니다.");
      return;
    }
    setError("");
    setPaying(true);
    try {
      const res = await checkout(selectedAddr);
      window.dispatchEvent(new Event("cart-change"));
      navigate("/me", { state: { tab: "orders", message: `결제 완료! 잔여 포인트: ${res.points_after?.toLocaleString()}점` } });
    } catch (err) {
      setError(err.message);
    } finally {
      setPaying(false);
    }
  };

  if (loading) return <p className="status-msg">불러오는 중...</p>;

  const items  = cart?.items ?? [];
  const total  = cart?.total ?? 0;
  const canPay = selectedAddr && total <= points && items.length > 0 && !items.some(i => i.stock === 0);

  return (
    <div className="checkout-page">
      <h2>주문 / 결제</h2>
      {error && <p className="auth-error">{error}</p>}

      {/* 주문 상품 */}
      <section className="checkout-section">
        <h3>주문 상품 ({items.length}개)</h3>
        <div className="checkout-items">
          {items.map(item => (
            <div key={item.product_id} className="checkout-item">
              <img src={item.image_url} alt={item.name} />
              <div className="checkout-item-info">
                <p className="checkout-item-name">{item.name}</p>
                <p className="checkout-item-sub">{item.sale_price?.toLocaleString()}원 × {item.quantity}</p>
              </div>
              <p className="checkout-item-price">{item.total_price?.toLocaleString()}원</p>
            </div>
          ))}
        </div>
      </section>

      {/* 배송지 */}
      <section className="checkout-section">
        <h3>배송지</h3>

        {addresses.length === 0 && !showAddForm && (
          <p className="checkout-hint">등록된 배송지가 없습니다. 새 배송지를 추가해주세요.</p>
        )}

        {addresses.length > 0 && (
          <div className="addr-list">
            {addresses.map(addr => (
              <label key={addr.id} className={`addr-card ${selectedAddr === addr.id ? "addr-card--selected" : ""}`}>
                <input
                  type="radio"
                  name="addr"
                  value={addr.id}
                  checked={selectedAddr === addr.id}
                  onChange={() => setSelectedAddr(addr.id)}
                />
                <div className="addr-card-body">
                  <span className="addr-name">{addr.recipient}</span>
                  {addr.is_default && <span className="addr-default-badge">기본</span>}
                  <p className="addr-detail">[{addr.zipcode}] {addr.address} {addr.address_detail}</p>
                  <p className="addr-phone">{addr.phone}</p>
                </div>
              </label>
            ))}
          </div>
        )}

        <button className="btn-add-addr" onClick={() => { setShowAddForm(v => !v); setError(""); }}>
          {showAddForm ? "취소" : "+ 새 배송지 추가"}
        </button>

        {showAddForm && (
          <form className="addr-form" onSubmit={handleAddAddress}>
            <div className="addr-form-row">
              <input placeholder="수령인 *" required value={addrForm.recipient}
                onChange={e => setAddrForm(f => ({ ...f, recipient: e.target.value }))} />
              <input placeholder="휴대폰 *" required value={addrForm.phone}
                onChange={e => setAddrForm(f => ({ ...f, phone: e.target.value }))} />
            </div>
            <div className="addr-form-row addr-search-row">
              <input placeholder="우편번호 *" readOnly value={addrForm.zipcode}
                onClick={openPostcode} className="addr-zipcode" />
              <button type="button" className="btn-postcode" onClick={openPostcode}>
                주소 검색
              </button>
            </div>
            <input placeholder="도로명 주소 *" readOnly value={addrForm.address}
              onClick={openPostcode} className="addr-road" />
            <input placeholder="상세 주소 (동/호수 등)" value={addrForm.address_detail}
              onChange={e => setAddrForm(f => ({ ...f, address_detail: e.target.value }))} />
            <button type="submit" className="btn-primary">배송지 저장</button>
          </form>
        )}
      </section>

      {/* 결제 정보 */}
      <section className="checkout-section checkout-payment">
        <h3>결제 정보</h3>
        <div className="payment-row">
          <span>상품 합계</span>
          <strong>{total.toLocaleString()}원</strong>
        </div>
        <div className="payment-row">
          <span>보유 포인트</span>
          <strong className={total > points ? "text-red" : ""}>{points.toLocaleString()}점</strong>
        </div>
        <div className="payment-row payment-row--total">
          <span>결제 후 잔여 포인트</span>
          <strong>{(points - total).toLocaleString()}점</strong>
        </div>
        {total > points && (
          <p className="checkout-hint text-red">포인트가 {(total - points).toLocaleString()}원 부족합니다.</p>
        )}
        <button
          className="btn-checkout"
          onClick={handleCheckout}
          disabled={!canPay || paying}
        >
          {paying ? "결제 중..." : `${total.toLocaleString()}원 포인트 결제`}
        </button>
        <button className="btn-back" onClick={() => navigate("/cart")}>
          장바구니로 돌아가기
        </button>
      </section>
    </div>
  );
}
