const BASE = import.meta.env.VITE_API_BASE;

// ── 공통 ────────────────────────────────────────────────────

function authHeaders() {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function req(method, path, body) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json", ...authHeaders() },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${BASE}${path}`, opts);
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "오류가 발생했습니다.");
  return data;
}

// ── 상품 ────────────────────────────────────────────────────

export async function fetchCategories(target = "") {
  const res = await fetch(`${BASE}/categories?target=${target}`);
  if (!res.ok) throw new Error("카테고리 조회 실패");
  return res.json();
}

export async function fetchProducts({ target = "", category_code = "", page = 1, page_size = 20, sort_by = "", q = "" } = {}) {
  const params = new URLSearchParams({ target, category_code, page, page_size, sort_by, q });
  const res = await fetch(`${BASE}/products?${params}`);
  if (!res.ok) throw new Error("상품 목록 조회 실패");
  return res.json();
}

export async function fetchSuggest(q) {
  if (!q) return { suggestions: [] };
  const res = await fetch(`${BASE}/products/suggest?q=${encodeURIComponent(q)}`);
  if (!res.ok) return { suggestions: [] };
  return res.json();
}

export async function fetchProduct(product_id) {
  const res = await fetch(`${BASE}/products/${product_id}`);
  if (!res.ok) throw new Error("상품 상세 조회 실패");
  return res.json();
}

// ── 인증 ────────────────────────────────────────────────────

export async function register(username, email, password) {
  return req("POST", "/auth/register", { username, email, password });
}

export async function login(email, password) {
  return req("POST", "/auth/login", { email, password });
}

// ── 내 정보 ─────────────────────────────────────────────────

export async function getMe()        { return req("GET", "/me"); }
export async function getMyPoints()  { return req("GET", "/me/points"); }
export async function getMyOrders()  { return req("GET", "/me/orders"); }
export async function getAddresses() { return req("GET", "/me/addresses"); }

export async function addAddress(body) {
  return req("POST", "/me/addresses", body);
}
export async function setDefaultAddress(id) {
  return req("PUT", `/me/addresses/${id}/default`);
}
export async function deleteAddress(id) {
  return req("DELETE", `/me/addresses/${id}`);
}

// ── 장바구니 ────────────────────────────────────────────────

export async function getCart()                          { return req("GET", "/cart"); }
export async function addToCart(product_id, quantity=1)  { return req("POST", "/cart", { product_id, quantity }); }
export async function updateCart(product_id, quantity)   { return req("PUT", `/cart/${product_id}`, { quantity }); }
export async function removeFromCart(product_id)         { return req("DELETE", `/cart/${product_id}`); }
export async function clearCart()                        { return req("DELETE", "/cart"); }
export async function checkout(address_id = 0)           { return req("POST", "/cart/checkout", { address_id }); }
export async function cancelOrder(order_id)              { return req("POST", `/orders/${order_id}/cancel`); }

// ── 관리자 ──────────────────────────────────────────────────

export async function adminGetProducts(page=1, page_size=50, q="", sort_by="", search_by="") {
  return req("GET", `/admin/products?page=${page}&page_size=${page_size}&q=${encodeURIComponent(q)}&sort_by=${sort_by}&search_by=${search_by}`);
}
export async function adminUpdateStock(product_id, stock) {
  return req("PUT", `/admin/products/${product_id}/stock`, { stock });
}
export async function adminDeleteProduct(product_id) {
  return req("DELETE", `/admin/products/${product_id}`);
}
export async function adminGetUsers() {
  return req("GET", "/admin/users");
}
export async function adminAdjustPoints(user_id, amount, description="") {
  return req("PUT", `/admin/users/${user_id}/points`, { amount, description });
}
export async function adminSetAdmin(user_id, is_admin) {
  return req("PUT", `/admin/users/${user_id}/admin`, { is_admin });
}
export async function adminDeleteUser(user_id) {
  return req("DELETE", `/admin/users/${user_id}`);
}
export async function adminRestoreUser(user_id) {
  return req("POST", `/admin/users/${user_id}/restore`);
}
export async function withdrawUser() {
  return req("DELETE", "/me");
}
export async function adminGetOrders() {
  return req("GET", "/admin/orders");
}
