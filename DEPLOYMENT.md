# PopGraph 部署指南

本文档介绍如何将 PopGraph 部署到生产环境。

## 目录

- [系统要求](#系统要求)
- [后端部署](#后端部署)
- [前端部署](#前端部署)
- [数据库配置](#数据库配置)
- [第三方服务配置](#第三方服务配置)
- [Docker 部署](#docker-部署)
- [监控与日志](#监控与日志)

## 系统要求

### 后端
- Python 3.11+
- PostgreSQL 14+
- Redis 6+

### 前端
- Node.js 18+
- 静态文件托管服务（Nginx/CDN）

## 后端部署

### 1. 环境准备

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制生产环境配置模板
cp .env.production.example .env.production

# 编辑配置文件，填入实际值
vim .env.production
```

关键配置项：
- `DATABASE_URL`: PostgreSQL 连接字符串
- `JWT_SECRET_KEY`: JWT 密钥（使用 `openssl rand -hex 32` 生成）
- `MODELSCOPE_API_KEY`: AI 模型 API 密钥
- 支付配置（支付宝/微信/银联）
- S3 存储配置
- 短信服务配置

### 3. 数据库迁移

```bash
# 运行数据库迁移
alembic upgrade head
```

### 4. 启动服务

使用 Gunicorn + Uvicorn workers：

```bash
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### 5. 启用定时任务

设置环境变量启用后台任务调度器：

```bash
export ENABLE_SCHEDULER=true
```

或者使用 cron 手动运行任务：

```bash
# 每小时检查订阅过期
0 * * * * cd /path/to/backend && python -m app.tasks.scheduler --task expiry

# 每天凌晨清理历史记录
0 2 * * * cd /path/to/backend && python -m app.tasks.scheduler --task cleanup
```

## 前端部署

### 1. 构建生产版本

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.production.example .env.production
vim .env.production

# 构建
npm run build
```

### 2. 部署静态文件

将 `dist/` 目录部署到静态文件服务器或 CDN。

Nginx 配置示例：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    root /var/www/popgraph/dist;
    index index.html;
    
    # SPA 路由支持
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # 静态资源缓存
    location /assets {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # API 代理
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 数据库配置

### PostgreSQL 设置

```sql
-- 创建数据库
CREATE DATABASE popgraph;

-- 创建用户
CREATE USER popgraph_user WITH PASSWORD 'your-password';

-- 授权
GRANT ALL PRIVILEGES ON DATABASE popgraph TO popgraph_user;
```

### Redis 设置

Redis 用于缓存和限流，确保 Redis 服务运行：

```bash
redis-server --daemonize yes
```

## 第三方服务配置

### 1. AI 模型 (ModelScope)

1. 注册 [ModelScope](https://modelscope.cn/) 账号
2. 获取 API Key
3. 配置 `MODELSCOPE_API_KEY`

### 2. 短信服务

#### 阿里云短信
1. 开通阿里云短信服务
2. 创建签名和模板
3. 获取 AccessKey
4. 配置相关环境变量

#### 腾讯云短信
1. 开通腾讯云短信服务
2. 创建应用和模板
3. 获取 SecretId/SecretKey
4. 配置相关环境变量

### 3. 支付服务

#### 支付宝
1. 注册支付宝开放平台
2. 创建应用并获取 AppID
3. 配置密钥对
4. 设置回调地址

#### 微信支付
1. 注册微信支付商户
2. 获取商户号和 API 密钥
3. 下载证书
4. 设置回调地址

#### 银联支付
1. 注册银联商户
2. 获取商户号和证书
3. 设置回调地址

### 4. S3 存储

支持 AWS S3 或兼容服务（阿里云 OSS、MinIO 等）：

1. 创建存储桶
2. 配置访问权限
3. 获取访问密钥
4. 可选：配置 CDN 加速

## Docker 部署

### docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/popgraph
      - REDIS_URL=redis://redis:6379/0
      - ENABLE_SCHEDULER=true
    depends_on:
      - db
      - redis
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

  db:
    image: postgres:14
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=popgraph
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:6
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### 启动服务

```bash
docker-compose up -d
```

## 监控与日志

### 日志配置

后端日志输出到 stdout，可使用日志收集工具（如 Fluentd、Logstash）收集。

### 健康检查

- 后端健康检查：`GET /health`
- 数据库连接检查：包含在健康检查中

### 错误追踪

推荐使用 Sentry 进行错误追踪：

1. 注册 Sentry 账号
2. 创建项目获取 DSN
3. 配置 `SENTRY_DSN` 环境变量

### 性能监控

推荐使用 Prometheus + Grafana 进行性能监控。

## 安全建议

1. **HTTPS**: 生产环境必须使用 HTTPS
2. **密钥管理**: 使用密钥管理服务（如 AWS Secrets Manager）
3. **防火墙**: 限制数据库和 Redis 只允许内网访问
4. **CORS**: 配置具体的允许域名，不要使用 `*`
5. **限流**: 配置 API 限流防止滥用
6. **备份**: 定期备份数据库

## 故障排查

### 常见问题

1. **数据库连接失败**
   - 检查 DATABASE_URL 配置
   - 确认数据库服务运行中
   - 检查防火墙规则

2. **支付回调失败**
   - 确认回调 URL 可公网访问
   - 检查签名验证配置
   - 查看支付平台日志

3. **图片上传失败**
   - 检查 S3 配置和权限
   - 确认存储桶策略正确
   - 检查网络连接

4. **短信发送失败**
   - 检查短信服务配置
   - 确认签名和模板已审核通过
   - 检查账户余额
