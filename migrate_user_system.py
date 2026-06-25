"""
数据库迁移脚本：添加用户系统
- 新建 user 表
- 新建 verification_code 表
- 给 comment 表添加 user_id 列
"""
import sqlite3
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'movie_review.db')


def migrate():
    if not os.path.exists(DB_PATH):
        print('[跳过] 数据库文件不存在，请直接启动应用由 create_all 自动建表')
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. 新建 user 表
    try:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS "user" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone VARCHAR(20) UNIQUE,
                email VARCHAR(128) UNIQUE,
                password_hash VARCHAR(256) NOT NULL,
                nickname VARCHAR(64) NOT NULL,
                avatar VARCHAR(256),
                created_at DATETIME
            )
        ''')
        print('[OK] user 表已创建')
    except Exception as e:
        print(f'[user 表] {e}')

    # 2. 新建 verification_code 表
    try:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS verification_code (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target VARCHAR(128) NOT NULL,
                code VARCHAR(10) NOT NULL,
                purpose VARCHAR(32) NOT NULL,
                expires_at DATETIME NOT NULL,
                used BOOLEAN DEFAULT 0,
                created_at DATETIME
            )
        ''')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_vc_target ON verification_code (target)')
        print('[OK] verification_code 表已创建')
    except Exception as e:
        print(f'[verification_code 表] {e}')

    # 3. 给 comment 表添加 user_id 列
    try:
        # 检查列是否已存在
        cur.execute('PRAGMA table_info(comment)')
        columns = [row[1] for row in cur.fetchall()]
        if 'user_id' not in columns:
            cur.execute('ALTER TABLE comment ADD COLUMN user_id INTEGER REFERENCES "user"(id)')
            print('[OK] comment 表已添加 user_id 列')
        else:
            print('[跳过] comment.user_id 列已存在')
    except Exception as e:
        print(f'[comment 表] {e}')

    conn.commit()
    conn.close()
    print('\n迁移完成！')


if __name__ == '__main__':
    migrate()
