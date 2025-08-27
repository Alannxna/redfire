-- RedFire MySQL 初始化脚本
-- ===========================

-- 设置字符集
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建用户和授权
CREATE USER IF NOT EXISTS 'redfire'@'%' IDENTIFIED BY 'redfire123';
GRANT ALL PRIVILEGES ON vnpy.* TO 'redfire'@'%';

-- 创建只读用户 (用于从库)
CREATE USER IF NOT EXISTS 'readonly'@'%' IDENTIFIED BY 'readonly123';
GRANT SELECT ON vnpy.* TO 'readonly'@'%';

-- 刷新权限
FLUSH PRIVILEGES;

-- 使用数据库
USE vnpy;

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_created_at (created_at),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建交易策略表
CREATE TABLE IF NOT EXISTS trading_strategies (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    strategy_type VARCHAR(50) NOT NULL,
    parameters JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_strategy_type (strategy_type),
    INDEX idx_is_active (is_active),
    INDEX idx_user_active (user_id, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建交易订单表
CREATE TABLE IF NOT EXISTS trading_orders (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    strategy_id BIGINT NULL,
    symbol VARCHAR(20) NOT NULL,
    side ENUM('BUY', 'SELL') NOT NULL,
    order_type ENUM('MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT') NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 8) NULL,
    status ENUM('PENDING', 'PARTIAL', 'FILLED', 'CANCELLED', 'REJECTED') NOT NULL DEFAULT 'PENDING',
    filled_quantity DECIMAL(20, 8) DEFAULT 0,
    avg_price DECIMAL(20, 8) NULL,
    commission DECIMAL(20, 8) DEFAULT 0,
    order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (strategy_id) REFERENCES trading_strategies(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_strategy_id (strategy_id),
    INDEX idx_symbol (symbol),
    INDEX idx_status (status),
    INDEX idx_order_time (order_time DESC),
    INDEX idx_user_symbol (user_id, symbol),
    INDEX idx_user_time (user_id, order_time DESC),
    INDEX idx_symbol_time (symbol, order_time DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建持仓表
CREATE TABLE IF NOT EXISTS positions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    quantity DECIMAL(20, 8) NOT NULL,
    avg_price DECIMAL(20, 8) NOT NULL,
    market_value DECIMAL(20, 2) NULL,
    unrealized_pnl DECIMAL(20, 2) NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_symbol (user_id, symbol),
    INDEX idx_user_id (user_id),
    INDEX idx_symbol (symbol),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建账户资金表
CREATE TABLE IF NOT EXISTS account_balance (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'CNY',
    total_balance DECIMAL(20, 2) NOT NULL DEFAULT 0,
    available_balance DECIMAL(20, 2) NOT NULL DEFAULT 0,
    frozen_balance DECIMAL(20, 2) NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_currency (user_id, currency),
    INDEX idx_user_id (user_id),
    INDEX idx_currency (currency)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    description TEXT,
    config_type ENUM('STRING', 'INTEGER', 'FLOAT', 'BOOLEAN', 'JSON') DEFAULT 'STRING',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_config_key (config_key),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入默认管理员用户
INSERT IGNORE INTO users (username, email, password_hash, is_superuser) 
VALUES ('admin', 'admin@redfire.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiDz4WiRwTGm', TRUE);

-- 插入默认系统配置
INSERT IGNORE INTO system_config (config_key, config_value, description, config_type) VALUES
('system.version', '1.0.0', 'RedFire系统版本', 'STRING'),
('trading.max_orders_per_user', '1000', '每用户最大订单数', 'INTEGER'),
('trading.max_position_size', '1000000.00', '最大持仓金额', 'FLOAT'),
('system.maintenance_mode', 'false', '系统维护模式', 'BOOLEAN'),
('cache.default_ttl', '3600', '默认缓存过期时间(秒)', 'INTEGER');

-- 创建触发器：更新持仓时自动计算市值
DELIMITER $$
CREATE TRIGGER IF NOT EXISTS update_position_value 
BEFORE UPDATE ON positions
FOR EACH ROW
BEGIN
    -- 这里可以添加市值计算逻辑
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END$$

-- 创建触发器：订单状态变更时更新持仓
CREATE TRIGGER IF NOT EXISTS update_position_on_order_fill
AFTER UPDATE ON trading_orders
FOR EACH ROW
BEGIN
    IF NEW.status = 'FILLED' AND OLD.status != 'FILLED' THEN
        -- 这里可以添加持仓更新逻辑
        INSERT INTO positions (user_id, symbol, quantity, avg_price) 
        VALUES (NEW.user_id, NEW.symbol, 
                CASE WHEN NEW.side = 'BUY' THEN NEW.filled_quantity ELSE -NEW.filled_quantity END,
                NEW.avg_price)
        ON DUPLICATE KEY UPDATE
            quantity = quantity + CASE WHEN NEW.side = 'BUY' THEN NEW.filled_quantity ELSE -NEW.filled_quantity END,
            avg_price = (avg_price * ABS(quantity) + NEW.avg_price * NEW.filled_quantity) / (ABS(quantity) + NEW.filled_quantity);
    END IF;
END$$
DELIMITER ;

-- 创建视图：用户交易统计
CREATE OR REPLACE VIEW user_trading_stats AS
SELECT 
    u.id as user_id,
    u.username,
    COUNT(DISTINCT o.id) as total_orders,
    COUNT(DISTINCT CASE WHEN o.status = 'FILLED' THEN o.id END) as filled_orders,
    SUM(CASE WHEN o.status = 'FILLED' THEN o.filled_quantity * o.avg_price END) as total_volume,
    COUNT(DISTINCT p.symbol) as active_positions,
    SUM(p.market_value) as total_position_value
FROM users u
LEFT JOIN trading_orders o ON u.id = o.user_id
LEFT JOIN positions p ON u.id = p.user_id AND ABS(p.quantity) > 0
WHERE u.is_active = TRUE
GROUP BY u.id, u.username;

-- 创建存储过程：清理旧订单数据
DELIMITER $$
CREATE PROCEDURE IF NOT EXISTS CleanOldOrders(IN days_to_keep INT)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    DELETE FROM trading_orders 
    WHERE order_time < DATE_SUB(NOW(), INTERVAL days_to_keep DAY)
    AND status IN ('FILLED', 'CANCELLED', 'REJECTED');
    
    COMMIT;
END$$
DELIMITER ;

-- 显示创建结果
SELECT 'RedFire数据库初始化完成!' as message;
SHOW TABLES;
