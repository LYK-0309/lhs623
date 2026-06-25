"""
数据库迁移脚本 - 手动执行
在 CloudBase 或本地数据库中执行以下 SQL 语句
"""

# SQLite 迁移 SQL（适用于本地开发）
SQLITE_MIGRATIONS = """
-- 1. 添加 User 表的 Base64 头像字段
ALTER TABLE user ADD COLUMN avatar_data TEXT;
ALTER TABLE user ADD COLUMN avatar_mime VARCHAR(64);

-- 2. 创建 Friendship 表（好友关系）
CREATE TABLE IF NOT EXISTS friendship (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    requester_id INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'pending',
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY (requester_id) REFERENCES user (id),
    FOREIGN KEY (receiver_id) REFERENCES user (id)
);
CREATE INDEX IF NOT EXISTS ix_friendship_requester_id ON friendship (requester_id);
CREATE INDEX IF NOT EXISTS ix_friendship_receiver_id ON friendship (receiver_id);

-- 3. 创建 Message 表（聊天消息）
CREATE TABLE IF NOT EXISTS message (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    message_type VARCHAR(32) DEFAULT 'text',
    related_movie_id INTEGER,
    created_at DATETIME,
    "read" BOOLEAN DEFAULT 0,
    FOREIGN KEY (sender_id) REFERENCES user (id),
    FOREIGN KEY (receiver_id) REFERENCES user (id),
    FOREIGN KEY (related_movie_id) REFERENCES movie (id)
);
CREATE INDEX IF NOT EXISTS ix_message_sender_id ON message (sender_id);
CREATE INDEX IF NOT EXISTS ix_message_receiver_id ON message (receiver_id);
CREATE INDEX IF NOT EXISTS ix_message_created_at ON message (created_at);
"""

# MySQL 迁移 SQL（适用于 CloudBase）
MYSQL_MIGRATIONS = """
-- 1. 添加 User 表的 Base64 头像字段
ALTER TABLE user ADD COLUMN IF NOT EXISTS avatar_data TEXT;
ALTER TABLE user ADD COLUMN IF NOT EXISTS avatar_mime VARCHAR(64);

-- 2. 创建 Friendship 表（好友关系）
CREATE TABLE IF NOT EXISTS friendship (
    id INT PRIMARY KEY AUTO_INCREMENT,
    requester_id INT NOT NULL,
    receiver_id INT NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_friendship_requester_id (requester_id),
    INDEX idx_friendship_receiver_id (receiver_id),
    FOREIGN KEY (requester_id) REFERENCES user (id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES user (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. 创建 Message 表（聊天消息）
CREATE TABLE IF NOT EXISTS message (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    content TEXT NOT NULL,
    message_type VARCHAR(32) DEFAULT 'text',
    related_movie_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    `read` BOOLEAN DEFAULT FALSE,
    INDEX idx_message_sender_id (sender_id),
    INDEX idx_message_receiver_id (receiver_id),
    INDEX idx_message_created_at (created_at),
    FOREIGN KEY (sender_id) REFERENCES user (id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES user (id) ON DELETE CASCADE,
    FOREIGN KEY (related_movie_id) REFERENCES movie (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

if __name__ == '__main__':
    print("=== SQLite 迁移 SQL ===")
    print(SQLITE_MIGRATIONS)
    print("\n=== MySQL 迁移 SQL ===")
    print(MYSQL_MIGRATIONS)
