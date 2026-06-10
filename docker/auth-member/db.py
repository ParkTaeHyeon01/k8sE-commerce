import os
import pymysql
import pymysql.cursors

_DB_CONFIG = {
    "host":     os.environ.get("MARIADB_HOST", "localhost"),
    "user":     os.environ.get("MARIADB_USER", "root"),
    "password": os.environ.get("MARIADB_PASSWORD", "pass123#"),
    "db":       os.environ.get("MARIADB_DB", "ecommerce"),
    "charset":  "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": True,
}


def get_conn():
    return pymysql.connect(**_DB_CONFIG)


def init_db():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id            INT          NOT NULL AUTO_INCREMENT,
                    username      VARCHAR(50)  NOT NULL,
                    email         VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    points        INT          NOT NULL DEFAULT 100000,
                    is_admin      TINYINT(1)   NOT NULL DEFAULT 0,
                    is_active     TINYINT(1)   NOT NULL DEFAULT 1,
                    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (id),
                    INDEX idx_email (email)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS point_history (
                    id          INT          NOT NULL AUTO_INCREMENT,
                    user_id     INT          NOT NULL,
                    amount      INT          NOT NULL,
                    description VARCHAR(255) NOT NULL,
                    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (id),
                    INDEX idx_user_id (user_id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            cur.execute("""
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
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id            INT          NOT NULL AUTO_INCREMENT,
                    user_id       INT          NOT NULL,
                    product_id    VARCHAR(50)  NOT NULL,
                    product_name  VARCHAR(255) NOT NULL,
                    product_image VARCHAR(512) NOT NULL DEFAULT '',
                    quantity      INT          NOT NULL DEFAULT 1,
                    unit_price    INT          NOT NULL,
                    total_price   INT          NOT NULL,
                    status        VARCHAR(20)  NOT NULL DEFAULT 'paid',
                    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (id),
                    INDEX idx_user_id (user_id),
                    INDEX idx_status (status),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
    finally:
        conn.close()


def seed_admin():
    import bcrypt as _bcrypt
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = 'admin@admin.com'")
            if not cur.fetchone():
                hashed = _bcrypt.hashpw("k8spass#".encode(), _bcrypt.gensalt()).decode()
                cur.execute(
                    "INSERT INTO users (username, email, password_hash, points, is_admin) VALUES (%s, %s, %s, %s, %s)",
                    ("admin", "admin@admin.com", hashed, 0, 1),
                )
    finally:
        conn.close()
