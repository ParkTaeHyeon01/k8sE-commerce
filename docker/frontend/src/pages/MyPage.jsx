import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { getMe, getMyOrders, getAddresses, addAddress, setDefaultAddress, deleteAddress, cancelOrder, withdrawUser } from "../api";
import { isLoggedIn, removeToken } from "../auth";

const TABS = ["내 정보", "주문 내역", "배송지 관리"];

export default function MyPage() {
  const navigate   = useNavigate();
  const location   = useLocation();
  const [tab, setTab]       = useState(location.state?.tab === "orders" ? "주문 내역" : "내 정보");
  const [me, setMe]         = useState(null);
  const [orders, setOrders] = useState([]);
  const [addresses, setAddresses] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [addrForm, setAddrForm] = useState({ recipient:"", phone:"", zipcode:"", address:"", address_detail:"" });
  const [message, setMessage] = useState(location.state?.message ?? "");

  useEffect(() => {
    if (!isLoggedIn()) { navigate("/login"); return; }
    loadMe();
    if (tab === "주문 내역") loadOrders();
  }, []);

  useEffect(() => {
    if (tab === "주문 내역") loadOrders();
    if (tab === "배송지 관리") loadAddresses();
  }, [tab]);

  const loadMe = async () => {
    try {
      const data = await getMe();
      setMe(data);
    } catch { navigate("/login"); }
  };

  const loadOrders = async () => {
    const data = await getMyOrders();
    setOrders(data.orders ?? []);
  };

  const loadAddresses = async () => {
    const data = await getAddresses();
    setAddresses(data.addresses);
  };

  const handleCancelOrder = async (order_id) => {
    if (!confirm("주문을 취소하시겠습니까?")) return;
    try {
      const res = await cancelOrder(order_id);
      setMessage(`취소 완료. 환불 포인트: ${res.refund_amount?.toLocaleString()}점`);
      loadOrders();
      loadMe();
    } catch (err) {
      setMessage(err.message);
    }
  };

  const handleAddAddress = async (e) => {
    e.preventDefault();
    try {
      await addAddress(addrForm);
      setShowAddForm(false);
      setAddrForm({ recipient:"", phone:"", zipcode:"", address:"", address_detail:"" });
      loadAddresses();
    } catch (err) {
      setMessage(err.message);
    }
  };

  const openPostcode = (setForm) => {
    if (!window.daum?.Postcode) { alert("주소 검색 스크립트를 불러오지 못했습니다."); return; }
    new window.daum.Postcode({
      oncomplete(data) {
        setForm(f => ({ ...f, zipcode: data.zonecode, address: data.roadAddress || data.jibunAddress }));
      },
    }).open();
  };

  const handleLogout = () => {
    removeToken();
    navigate("/");
  };

  const handleWithdraw = async () => {
    if (!confirm("정말 탈퇴하시겠습니까?\n탈퇴 후에는 재가입만 가능하며 계정을 복구할 수 없습니다.")) return;
    try {
      await withdrawUser();
      removeToken();
      navigate("/", { state: { message: "탈퇴가 완료되었습니다." } });
    } catch (err) {
      setMessage(err.message);
    }
  };

  return (
    <div className="mypage">
      <div className="mypage-tabs">
        {TABS.map(t => (
          <button key={t} className={`mypage-tab ${tab === t ? "active" : ""}`} onClick={() => setTab(t)}>{t}</button>
        ))}
      </div>
      {message && <p className="mypage-message">{message}</p>}

      {tab === "내 정보" && me && (
        <div className="mypage-section">
          <h3>내 정보</h3>
          <table className="info-table">
            <tbody>
              <tr><td>이름</td><td>{me.username}</td></tr>
              <tr><td>이메일</td><td>{me.email}</td></tr>
              <tr><td>포인트</td><td><strong>{me.points?.toLocaleString()}점</strong></td></tr>
              <tr><td>가입일</td><td>{me.created_at}</td></tr>
            </tbody>
          </table>
          <div className="mypage-actions">
            <button className="btn-mypage-logout" onClick={handleLogout}>로그아웃</button>
            <button className="btn-withdraw" onClick={handleWithdraw}>회원 탈퇴</button>
          </div>
        </div>
      )}

      {tab === "주문 내역" && (
        <div className="mypage-section">
          <h3>주문 내역</h3>
          {orders.length === 0 ? <p>주문 내역이 없습니다.</p> : (
            <div className="order-list">
              {orders.map(o => (
                <div key={o.id} className={`order-item ${o.status === "cancelled" ? "cancelled" : ""}`}>
                  <img src={o.product_image} alt={o.product_name} onClick={() => navigate(`/products/${o.product_id}`)} />
                  <div className="order-info">
                    <p className="order-name">{o.product_name}</p>
                    <p>{o.quantity}개 | {o.total_price?.toLocaleString()}원</p>
                    {o.shipping_address && <p className="order-addr">{o.shipping_address}</p>}
                    <p className="order-date">{o.created_at}</p>
                  </div>
                  <div className="order-status">
                    {o.status === "paid"
                      ? <><span className="badge-paid">결제완료</span><button className="btn-cancel" onClick={() => handleCancelOrder(o.id)}>취소</button></>
                      : <span className="badge-cancelled">취소됨</span>
                    }
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === "배송지 관리" && (
        <div className="mypage-section">
          <h3>배송지 관리</h3>
          <button className="btn-primary" onClick={() => setShowAddForm(v => !v)}>+ 배송지 추가</button>
          {showAddForm && (
            <form onSubmit={handleAddAddress} className="addr-form">
              <div className="addr-form-row">
                <input placeholder="수령인 *" required value={addrForm.recipient} onChange={e => setAddrForm(f => ({...f, recipient: e.target.value}))} />
                <input placeholder="휴대폰 *" required value={addrForm.phone} onChange={e => setAddrForm(f => ({...f, phone: e.target.value}))} />
              </div>
              <div className="addr-form-row addr-search-row">
                <input placeholder="우편번호 *" readOnly value={addrForm.zipcode}
                  onClick={() => openPostcode(setAddrForm)} className="addr-zipcode" />
                <button type="button" className="btn-postcode" onClick={() => openPostcode(setAddrForm)}>주소 검색</button>
              </div>
              <input placeholder="도로명 주소 *" readOnly value={addrForm.address}
                onClick={() => openPostcode(setAddrForm)} className="addr-road" />
              <input placeholder="상세 주소 (동/호수 등)" value={addrForm.address_detail}
                onChange={e => setAddrForm(f => ({...f, address_detail: e.target.value}))} />
              <button type="submit" className="btn-primary">저장</button>
            </form>
          )}
          <div className="addr-list">
            {addresses.map(a => (
              <div key={a.id} className={`addr-item ${a.is_default ? "default" : ""}`}>
                <div className="addr-info">
                  {a.is_default && <span className="badge-default">기본</span>}
                  <strong>{a.recipient}</strong> {a.phone}
                  <p>[{a.zipcode}] {a.address} {a.address_detail}</p>
                </div>
                <div className="addr-actions">
                  {!a.is_default && <button onClick={() => { setDefaultAddress(a.id).then(loadAddresses); }}>기본 설정</button>}
                  <button onClick={() => { deleteAddress(a.id).then(loadAddresses); }}>삭제</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
