import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { register } from "../api";
import { saveToken } from "../auth";

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm]     = useState({ username: "", email: "", password: "", confirm: "" });
  const [error, setError]   = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (form.password !== form.confirm) {
      setError("비밀번호가 일치하지 않습니다.");
      return;
    }
    if (form.password.length < 8) {
      setError("비밀번호는 8자 이상이어야 합니다.");
      return;
    }
    setLoading(true);
    try {
      const res = await register(form.username, form.email, form.password);
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
        <h2>회원가입</h2>
        {error && <p className="auth-error">{error}</p>}
        <form onSubmit={handleSubmit} className="auth-form">
          <input
            type="text" placeholder="이름" required
            value={form.username} onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
          />
          <input
            type="email" placeholder="이메일" required
            value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
          />
          <input
            type="password" placeholder="비밀번호 (8자 이상)" required
            value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
          />
          <input
            type="password" placeholder="비밀번호 확인" required
            value={form.confirm} onChange={e => setForm(f => ({ ...f, confirm: e.target.value }))}
          />
          <button type="submit" disabled={loading}>
            {loading ? "가입 중..." : "회원가입"}
          </button>
        </form>
        <p className="auth-footer">
          이미 계정이 있으신가요? <Link to="/login">로그인</Link>
        </p>
      </div>
    </div>
  );
}
