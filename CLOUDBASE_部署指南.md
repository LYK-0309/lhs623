# CloudBase 部署配置指导

## 1. 邮箱验证码配置（必需）

CloudBase 生产环境需要配置以下环境变量才能发送 QQ 邮箱验证码：

### 步骤 1：获取 QQ 邮箱 SMTP 授权码
1. 登录 QQ 邮箱
2. 进入"设置" → "账户"
3. 找到"POP3/IMAP/SMTP/Exchange/CardDAV服务"
4. 开启"IMAP/SMTP服务"或"POP3/SMTP服务"
5. 按提示用手机发送短信获取**授权码**（不是 QQ 密码）

### 步骤 2：在 CloudBase 控制台配置环境变量
1. 登录 [腾讯云 CloudBase 控制台](https://console.cloud.tencent.com/tcb)
2. 选择你的云托管服务
3. 进入"环境变量"配置页面
4. 添加以下环境变量：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `MAIL_USERNAME` | 你的 QQ 邮箱（如：123456789@qq.com） | 发件人邮箱 |
| `MAIL_PASSWORD` | 第1步获取的 SMTP 授权码 | 不是 QQ 密码！ |
| `MAIL_SERVER` | smtp.qq.com | QQ 邮箱 SMTP 服务器（默认值） |
| `MAIL_PORT` | 465 | SSL 端口（默认值） |
| `MAIL_USE_SSL` | true | 使用 SSL 加密（默认值） |

### 步骤 3：重新部署
配置完环境变量后，需要重新部署应用才能生效。

---

## 2. 数据库迁移（必需）

### 本地开发环境（SQLite）
应用启动时会自动执行迁移，无需手动操作。

### CloudBase 生产环境（MySQL）
如果之前已经部署过，需要手动执行以下 SQL 语句：

```sql
-- 1. 添加 User 表的 Base64 头像字段
ALTER TABLE `user` ADD COLUMN IF NOT EXISTS `avatar_data` TEXT;
ALTER TABLE `user` ADD COLUMN IF NOT EXISTS `avatar_mime` VARCHAR(64);

-- 2. 创建 Friendship 表（好友关系）
CREATE TABLE IF NOT EXISTS `friendship` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `requester_id` INT NOT NULL,
    `receiver_id` INT NOT NULL,
    `status` VARCHAR(16) NOT NULL DEFAULT 'pending',
    `created_at` DATETIME,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_friendship_requester_id` (`requester_id`),
    INDEX `idx_friendship_receiver_id` (`receiver_id`),
    FOREIGN KEY (`requester_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`receiver_id`) REFERENCES `user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. 创建 Message 表（聊天消息）
CREATE TABLE IF NOT EXISTS `message` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `sender_id` INT NOT NULL,
    `receiver_id` INT NOT NULL,
    `content` TEXT NOT NULL,
    `message_type` VARCHAR(32) DEFAULT 'text',
    `related_movie_id` INT,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `read` BOOLEAN DEFAULT FALSE,
    INDEX `idx_message_sender_id` (`sender_id`),
    INDEX `idx_message_receiver_id` (`receiver_id`),
    INDEX `idx_message_created_at` (`created_at`),
    FOREIGN KEY (`sender_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`receiver_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`related_movie_id`) REFERENCES `movie` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**执行方式：**
1. 登录 CloudBase 控制台
2. 进入"数据库"管理页面
3. 点击"SQL 操作"或"phpMyAdmin"
4. 粘贴上述 SQL 语句并执行

---

## 3. 头像上传说明

### 问题原因
CloudBase 云托管的容器文件系统是**临时的**，上传的文件在重新部署后会丢失。

### 解决方案
已将头像存储改为 **Base64 编码存入数据库**，彻底解决此问题：
- 用户上传的头像会自动转为 Base64 字符串
- 存储在 `user.avatar_data` 字段中
- 通过 `data:image/xxx;base64,xxx` 格式直接显示在页面上
- 不依赖文件系统，重新部署后头像不会丢失

---

## 4. 新增功能说明

### 账号注销
- 入口：个人资料页 → 底部"危险操作"区 → "注销账号"
- 需要输入密码 + 输入"确认注销"文字双重确认
- 注销后所有数据（影评、好友关系）一并删除

### 加好友功能
- 入口：导航栏用户菜单 → "我的好友"
- 功能：搜索用户、发送好友请求、接受/拒绝请求、删除好友

### 好友聊天
- 入口：我的好友 → 点击好友旁的"聊天"按钮
- 功能：实时聊天（每3秒自动刷新）、消息已读标记

### 分享影视给好友
- 入口：影视详情页 → "分享给好友"按钮
- 功能：选择好友，发送带链接的分享消息

---

## 5. 部署检查清单

- [ ] 配置 CloudBase 环境变量（MAIL_USERNAME、MAIL_PASSWORD）
- [ ] 执行数据库迁移 SQL（如果是更新部署）
- [ ] 重新部署应用
- [ ] 测试注册/登录功能
- [ ] 测试头像上传功能
- [ ] 测试加好友功能
- [ ] 测试聊天功能
- [ ] 测试分享影视功能
- [ ] 测试账号注销功能
