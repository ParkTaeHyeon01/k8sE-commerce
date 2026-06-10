// JWT 파싱 및 인증 상태 헬퍼

export function getToken() {
  return localStorage.getItem("token");
}

export function saveToken(token) {
  localStorage.setItem("token", token);
}

export function removeToken() {
  localStorage.removeItem("token");
}

export function getUser() {
  const token = getToken();
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    if (payload.exp * 1000 < Date.now()) {
      removeToken();
      return null;
    }
    return payload;
  } catch {
    return null;
  }
}

export function isLoggedIn() {
  return getUser() !== null;
}

export function isAdmin() {
  return getUser()?.is_admin === true;
}
