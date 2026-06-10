-- ============================================================
-- 초기 데이터 (관리자 계정)
-- 비밀번호: k8spass# (bcrypt 해시, 서비스 시작 시 자동 시드됨)
-- 이 파일은 참고용 — 실제 시드는 auth-member 서비스가 자동 처리
-- ============================================================

USE ecommerce;

INSERT IGNORE INTO users (username, email, password_hash, points, is_admin)
VALUES ('admin', 'admin@admin.com', '$2b$12$placeholder', 0, 1);
