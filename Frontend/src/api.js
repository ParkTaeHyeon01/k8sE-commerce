const BASE = import.meta.env.VITE_API_BASE;

export async function fetchCategories(target = "") {
  const res = await fetch(`${BASE}/categories?target=${target}`);
  if (!res.ok) throw new Error("카테고리 조회 실패");
  return res.json();
}

export async function fetchProducts({ target = "", category_code = "", page = 1, page_size = 20, sort_by = "" } = {}) {
  const params = new URLSearchParams({ target, category_code, page, page_size, sort_by });
  const res = await fetch(`${BASE}/products?${params}`);
  if (!res.ok) throw new Error("상품 목록 조회 실패");
  return res.json();
}

export async function fetchProduct(product_id) {
  const res = await fetch(`${BASE}/products/${product_id}`);
  if (!res.ok) throw new Error("상품 상세 조회 실패");
  return res.json();
}
