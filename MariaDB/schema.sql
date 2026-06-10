-- ============================================================
-- k8s E-Commerce 데이터베이스 스키마
-- ============================================================

CREATE DATABASE IF NOT EXISTS ecommerce DEFAULT CHARACTER SET utf8mb4;
USE ecommerce;

-- 회원
CREATE TABLE IF NOT EXISTS users (
    id            INT          NOT NULL AUTO_INCREMENT,
    username      VARCHAR(50)  NOT NULL,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    points        INT          NOT NULL DEFAULT 100000,
    is_admin      TINYINT(1)   NOT NULL DEFAULT 0,
    is_active      TINYINT(1)   NOT NULL DEFAULT 1,
    deactivated_by VARCHAR(10)           DEFAULT NULL,  -- 'user'(탈퇴) | 'admin'(정지) | NULL(활성)
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_email (email)
);

-- 포인트 내역
CREATE TABLE IF NOT EXISTS point_history (
    id          INT          NOT NULL AUTO_INCREMENT,
    user_id     INT          NOT NULL,
    amount      INT          NOT NULL,  -- 양수: 지급, 음수: 차감
    description VARCHAR(255) NOT NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_user_id (user_id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 배송지
CREATE TABLE IF NOT EXISTS shipping_addresses (
    id             INT          NOT NULL AUTO_INCREMENT,
    user_id        INT          NOT NULL,
    recipient      VARCHAR(50)  NOT NULL,
    phone          VARCHAR(20)  NOT NULL,
    zipcode        VARCHAR(10)  NOT NULL,
    address        VARCHAR(255) NOT NULL,
    address_detail VARCHAR(255) NOT NULL DEFAULT '',
    is_default     TINYINT(1)   NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    INDEX idx_user_id (user_id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 주문
CREATE TABLE IF NOT EXISTS orders (
    id               INT          NOT NULL AUTO_INCREMENT,
    user_id          INT          NOT NULL,
    product_id       VARCHAR(50)  NOT NULL,
    product_name     VARCHAR(255) NOT NULL,
    product_image    VARCHAR(512) NOT NULL DEFAULT '',
    quantity         INT          NOT NULL DEFAULT 1,
    unit_price       INT          NOT NULL,
    total_price      INT          NOT NULL,
    shipping_address VARCHAR(500)          DEFAULT '',
    status           VARCHAR(20)  NOT NULL DEFAULT 'paid',  -- paid | cancelled
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
