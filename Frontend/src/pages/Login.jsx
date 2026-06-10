import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { login } from "../api";
import { saveToken } from "../auth";

export default function Login() {
  const navigate = useNavigate();
  const [form, setForm]     = useState({ email: "", password: "" });
  const [error, setError]   = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await login(form.email, form.password);
      saveToken(res.token);
      window.dispatchEvent(new Event("auth-change"));
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-box">
        <h2>로그인</h2>
        {error && <p className="auth-error">{error}</p>}
        <form onSubmit={handleSubmit} className="auth-form">
          <input
            type="email" placeholder="이메일" required
            value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
          />
          <input
            type="password" placeholder="비밀번호" required
            value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
          />
          <button type="submit" disabled={loading}>
            {loading ? "로그인 중..." : "로그인"}
          </button>
        </form>
        <p className="auth-footer">
          계정이 없으신가요? <Link to="/register">회원가입</Link>
        </p>
      </div>
    </div>
  );
}
