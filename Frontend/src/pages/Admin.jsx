import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  adminGetProducts, adminUpdateStock, adminDeleteProduct,
  adminGetUsers, adminAdjustPoints, adminSetAdmin, adminDeleteUser, adminRestoreUser,
  adminGetOrders,
} from "../api";
import { isAdmin } from "../auth";

const TABS = ["상품 관리", "회원 관리", "주문 내역"];

export default function Admin() {
  const navigate = useNavigate();
  const [tab, setTab] = useState("상품 관리");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!isAdmin()) { navigate("/"); }
  }, []);

  return (
    <div className="admin-page">
      <h2>관리자 페이지</h2>
      <div className="admin-tabs">
        {TABS.map(t => (
          <button key={t} className={`admin-tab ${tab === t ? "active" : ""}`} onClick={() => { setTab(t); setMessage(""); }}>{t}</button>
        ))}
      </div>
      {message && <p className="admin-message">{message}</p>}
      {tab === "상품 관리"  && <ProductManagement setMessage={setMessage} />}
      {tab === "회원 관리"  && <UserManagement    setMessage={setMessage} />}
      {tab === "주문 내역"  && <OrderManagement   setMessage={setMessage} />}
    </div>
  );
}

// ── 상품 관리 ──────────────────────────────────────────────

function ProductManagement({ setMessage }) {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [editStock, setEditStock] = useState({});
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const PAGE_SIZE = 50;

  useEffect(() => { load(); }, [page]);

  const load = async () => {
    try {
      const data = await adminGetProducts(page, PAGE_SIZE);
      setProducts(data.products);
      setTotal(data.total);
    } catch (err) { setMessage(err.message); }
  };

  const handleUpdateStock = async (product_id) => {
    const stock = parseInt(editStock[product_id]);
    if (isNaN(stock) || stock < 0) { setMessage("유효한 재고를 입력하세요."); return; }
    try {
      await adminUpdateStock(product_id, stock);
      setMessage("재고가 업데이트되었습니다.");
      load();
    } catch (err) { setMessage(err.message); }
  };

  const handleDelete = async (product_id, name) => {
    if (!confirm(`'${name}' 상품을 삭제하시겠습니까?`)) return;
    try {
      await adminDeleteProduct(product_id);
      setMessage("상품이 삭제되었습니다.");
      load();
    } catch (err) { setMessage(err.message); }
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="admin-section">
      <p className="admin-total">전체 {total?.toLocaleString()}개</p>
      <table className="admin-table">
        <thead>
          <tr><th>상품명</th><th>카테고리</th><th>가격</th><th>할인율</th><th>재고</th><th>관리</th></tr>
        </thead>
        <tbody>
          {products.map(p => (
            <tr key={p.product_id}>
              <td className="product-name-cell" onClick={() => navigate(`/products/${p.product_id}`)}>{p.name}</td>
              <td>{p.category_name}</td>
              <td>{p.sale_price?.toLocaleString()}원</td>
              <td>{p.discount_rate > 0 ? `${p.discount_rate}%` : "-"}</td>
              <td>
                <div className="stock-edit">
                  <input
                    type="number" min="0"
                    defaultValue={p.stock}
                    onChange={e => setEditStock(s => ({ ...s, [p.product_id]: e.target.value }))}
                  />
                  <button onClick={() => handleUpdateStock(p.product_id)}>저장</button>
                </div>
              </td>
              <td>
                <button className="btn-danger" onClick={() => handleDelete(p.product_id, p.name)}>삭제</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {totalPages > 1 && (
        <div className="pagination">
          <button disabled={page === 1} onClick={() => setPage(p => p - 1)}>← 이전</button>
          <span>{page} / {totalPages}</span>
          <button disabled={page === totalPages} onClick={() => setPage(p => p + 1)}>다음 →</button>
        </div>
      )}
    </div>
  );
}

// ── 회원 관리 ──────────────────────────────────────────────

function UserManagement({ setMessage }) {
  const [users, setUsers]     = useState([]);
  const [pointInputs, setPointInputs] = useState({});

  useEffect(() => { load(); }, []);

  const load = async () => {
    try {
      const data = await adminGetUsers();
      setUsers(data.users);
    } catch (err) { setMessage(err.message); }
  };

  const handleAdjustPoints = async (user_id) => {
    const amount = parseInt(pointInputs[user_id]);
    if (isNaN(amount)) { setMessage("포인트 금액을 입력하세요."); return; }
    try {
      const res = await adminAdjustPoints(user_id, amount, "관리자 포인트 조정");
      setMessage(`포인트 조정 완료. 잔액: ${res.points_after?.toLocaleString()}점`);
      load();
    } catch (err) { setMessage(err.message); }
  };

  const handleSetAdmin = async (user_id, is_admin) => {
    if (!confirm(is_admin ? "관리자 권한을 부여하시겠습니까?" : "관리자 권한을 해제하시겠습니까?")) return;
    try {
      await adminSetAdmin(user_id, is_admin);
      setMessage("권한이 변경되었습니다.");
      load();
    } catch (err) { setMessage(err.message); }
  };

  const handleDelete = async (user_id, username) => {
    if (!confirm(`'${username}' 회원을 정지하시겠습니까?`)) return;
    try {
      await adminDeleteUser(user_id);
      setMessage("회원이 정지되었습니다.");
      load();
    } catch (err) { setMessage(err.message); }
  };

  const handleRestore = async (user_id, username) => {
    if (!confirm(`'${username}' 회원의 정지를 해제하시겠습니까?`)) return;
    try {
      await adminRestoreUser(user_id);
      setMessage("회원 정지가 해제되었습니다.");
      load();
    } catch (err) { setMessage(err.message); }
  };

  return (
    <div className="admin-section">
      <table className="admin-table">
        <thead>
          <tr><th>ID</th><th>이름</th><th>이메일</th><th>포인트</th><th>권한</th><th>상태</th><th>포인트 조정</th><th style={{width:"200px"}}>관리</th></tr>
        </thead>
        <tbody>
          {users.map(u => (
            <tr key={u.id} className={!u.is_active ? "inactive-row" : ""}>
              <td>{u.id}</td>
              <td>{u.username}</td>
              <td>{u.email}</td>
              <td>{u.points?.toLocaleString()}점</td>
              <td>{u.is_admin ? <span className="badge-admin">관리자</span> : "일반"}</td>
              <td>
                {u.is_active
                  ? <span className="badge-active">활성</span>
                  : u.deactivated_by === "admin"
                    ? <span className="badge-suspended">정지</span>
                    : <span className="badge-inactive">탈퇴</span>
                }
              </td>
              <td>
                <div className="point-edit">
                  <input
                    type="number" placeholder="±포인트"
                    onChange={e => setPointInputs(s => ({ ...s, [u.id]: e.target.value }))}
                  />
                  <button onClick={() => handleAdjustPoints(u.id)}>적용</button>
                </div>
              </td>
              <td>
                <div className="action-btns">
                  {!u.is_admin
                    ? <button onClick={() => handleSetAdmin(u.id, true)}>관리자 설정</button>
                    : <button onClick={() => handleSetAdmin(u.id, false)}>권한 해제</button>
                  }
                  {u.is_active && <button className="btn-danger" onClick={() => handleDelete(u.id, u.username)}>정지</button>}
                  {!u.is_active && u.deactivated_by === "admin" && (
                    <button className="btn-restore" onClick={() => handleRestore(u.id, u.username)}>정지 해제</button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── 주문 내역 ──────────────────────────────────────────────

function OrderManagement({ setMessage }) {
  const [orders, setOrders] = useState([]);

  useEffect(() => { load(); }, []);

  const load = async () => {
    try {
      const data = await adminGetOrders();
      setOrders(data.orders);
    } catch (err) { setMessage(err.message); }
  };

  return (
    <div className="admin-section">
      <p className="admin-total">전체 {orders.length}건</p>
      <table className="admin-table">
        <thead>
          <tr><th>주문ID</th><th>회원ID</th><th>상품명</th><th>수량</th><th>금액</th><th>상태</th><th>일시</th></tr>
        </thead>
        <tbody>
          {orders.map(o => (
            <tr key={o.id} className={o.status === "cancelled" ? "cancelled-row" : ""}>
              <td>{o.id}</td>
              <td>{o.user_id}</td>
              <td>{o.product_name}</td>
              <td>{o.quantity}</td>
              <td>{o.total_price?.toLocaleString()}원</td>
              <td>{o.status === "paid" ? <span className="badge-paid">결제완료</span> : <span className="badge-cancelled">취소됨</span>}</td>
              <td>{o.created_at}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
