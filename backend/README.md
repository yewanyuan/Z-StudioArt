# PopGraph Backend

爆款图 - AI 图文一体化生成平台后端服务

## 技术栈

- Python 3.11+
- FastAPI
- SQLAlchemy (PostgreSQL)
- Redis
- Pillow
- Hypothesis (属性测试)
- bcrypt (密码哈希)
- PyJWT (JWT Token)
- alipay-sdk-python (支付宝支付)
- wechatpayv3 (微信支付)
- boto3 (AWS S3 存储)

## 开发环境设置

### 安装依赖

```bash
cd backend
poetry install
```

### 运行开发服务器

```bash
poetry run uvicorn app.main:app --reload

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 运行测试

```bash
# 运行所有测试
poetry run pytest

# 运行单元测试
poetry run pytest tests/unit/

# 运行属性测试
poetry run pytest tests/property/

# 运行集成测试
poetry run pytest tests/integration/

# 运行测试并生成覆盖率报告
poetry run pytest --cov=app
```

## 项目结构

```
backend/
├── app/
│   ├── api/          # API 路由
│   ├── clients/      # 外部服务客户端
│   │   └── zimage_client.py  # Z-Image-Turbo AI 模型客户端
│   ├── core/         # 核心配置
│   ├── models/       # 数据库模型和 Schema
│   │   ├── database.py   # SQLAlchemy 模型 (User, RefreshToken, VerificationCode 等)
│   │   └── schemas.py    # Pydantic Schema 定义
│   ├── services/     # 业务服务
│   │   ├── auth_service.py      # 用户认证服务
│   │   ├── history_service.py   # 生成历史记录服务
│   │   ├── payment_service.py   # 支付订阅服务
│   │   └── sms_service.py       # 短信验证码服务
│   ├── tasks/        # 后台定时任务
│   │   ├── __init__.py       # 模块导出
│   │   └── scheduler.py      # 任务调度器（订阅过期检查、历史记录清理）
│   ├── utils/        # 工具模块
│   │   ├── jwt.py            # JWT Token 工具
│   │   └── prompt_builder.py # Prompt 构建器
│   └── main.py       # 应用入口
├── alembic/          # 数据库迁移
│   └── versions/     # 迁移脚本
├── tests/
│   ├── unit/         # 单元测试
│   ├── property/     # 属性测试
│   └── integration/  # 集成测试
├── conftest.py       # pytest 配置
└── pyproject.toml    # 项目配置
```

## 数据模型

### Pydantic Schemas (`app/models/schemas.py`)

已实现的核心 Schema：

| Schema | 用途 |
|--------|------|
| `PosterGenerationRequest` | 海报生成请求，支持中英文文案 |
| `PosterGenerationResponse` | 海报生成响应 |
| `GeneratedImage` | 生成的图像信息，包含 URL、尺寸、水印标记和可选的 Base64 数据 |
| `Template` / `PromptModifiers` | 预设商业模板定义 |
| `ContentFilterResult` | 敏感内容过滤结果 |
| `RateLimitResult` | 限流检查结果 |
| `SceneFusionRequest/Response` | 商品图场景融合，响应支持可选的 Base64 数据 |
| `GenerationOptions` | Z-Image-Turbo 生成选项 |

#### GeneratedImage 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | 是 | 图像唯一标识 |
| `url` | string | 是 | 图像 URL（推荐使用） |
| `thumbnail_url` | string | 是 | 缩略图 URL |
| `has_watermark` | bool | 是 | 是否有水印 |
| `width` | int | 是 | 图像宽度 |
| `height` | int | 是 | 图像高度 |
| `image_base64` | string | 否 | 图像 Base64 编码数据（可选） |

#### SceneFusionResponse 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `request_id` | string | 是 | 请求唯一标识 |
| `fused_image_url` | string | 是 | 融合后图像 URL |
| `processing_time_ms` | int | 是 | 处理时间（毫秒） |
| `image_base64` | string | 否 | 图像 Base64 编码数据（可选） |

### 枚举类型

- `MembershipTier`: 会员等级 (FREE/BASIC/PROFESSIONAL)
- `TemplateCategory`: 模板分类 (promotional/premium/holiday)
- `HolidayType`: 节日类型 (春节/情人节/双十一)
- `GenerationType`: 生成类型 (poster/scene_fusion)
- `PaymentMethod`: 支付方式 (alipay/wechat/unionpay)
- `PaymentStatus`: 支付状态 (pending/paid/failed/expired/refunded)
- `SubscriptionPlan`: 订阅计划 (basic_monthly/basic_yearly/pro_monthly/pro_yearly)

### SQLAlchemy 模型 (`app/models/database.py`)

- `User`: 用户模型，包含会员等级、使用配额和认证信息
- `GenerationRecord`: 生成记录
- `GeneratedImageRecord`: 生成图片记录，存储图片二进制数据
- `TemplateRecord`: 模板存储
- `RefreshToken`: 刷新令牌，用于 Token 管理和登出
- `VerificationCode`: 短信验证码记录
- `PaymentOrder`: 支付订单，存储订阅支付信息

#### User 认证相关字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `phone` | String(20) | 否 | 手机号（唯一索引） |
| `email` | String(255) | 否 | 邮箱地址（唯一索引） |
| `password_hash` | String(255) | 否 | 密码哈希（邮箱注册用户） |

#### RefreshToken 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | String(36) | 是 | 令牌唯一标识 (UUID) |
| `user_id` | String(36) | 是 | 关联的用户 ID (外键) |
| `token_hash` | String(255) | 是 | Token 的 SHA-256 哈希 |
| `expires_at` | DateTime | 是 | 过期时间 |
| `created_at` | DateTime | 是 | 创建时间 |
| `is_revoked` | Boolean | 是 | 是否已撤销 |

#### VerificationCode 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | String(36) | 是 | 验证码唯一标识 (UUID) |
| `phone` | String(20) | 是 | 手机号 |
| `code` | String(6) | 是 | 6 位数字验证码 |
| `expires_at` | DateTime | 是 | 过期时间 |
| `created_at` | DateTime | 是 | 创建时间 |
| `is_used` | Boolean | 是 | 是否已使用 |

#### GeneratedImageRecord 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | String(36) | 是 | 图片唯一标识 (UUID) |
| `generation_id` | String(36) | 是 | 关联的生成记录 ID (外键) |
| `image_data` | LargeBinary | 是 | 图片二进制数据 |
| `width` | Integer | 是 | 图片宽度 (像素) |
| `height` | Integer | 是 | 图片高度 (像素) |
| `has_watermark` | Boolean | 是 | 是否包含水印 |
| `created_at` | DateTime | 是 | 创建时间 |

**关系：**
- 多对一关联 `GenerationRecord`（通过 `generation_id` 外键）
- 级联删除：删除 `GenerationRecord` 时自动删除关联的图片记录

#### PaymentOrder 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | String(36) | 是 | 订单唯一标识 (UUID) |
| `user_id` | String(36) | 是 | 关联的用户 ID (外键) |
| `plan` | SubscriptionPlan | 是 | 订阅计划 |
| `method` | PaymentMethod | 是 | 支付方式 |
| `amount` | Integer | 是 | 金额（单位：分） |
| `status` | PaymentStatus | 是 | 支付状态，默认 PENDING |
| `external_order_id` | String(100) | 否 | 外部支付网关订单号 |
| `paid_at` | DateTime | 否 | 支付完成时间 |
| `created_at` | DateTime | 是 | 创建时间 |
| `updated_at` | DateTime | 是 | 更新时间 |

## API 路由模块

### PosterAPI (`app/api/poster.py`)

海报生成 API 模块，提供海报生成和配额查询端点。

| 端点 | 方法 | 功能 | 相关需求 |
|------|------|------|----------|
| `/api/poster/generate` | POST | 生成商业海报 | 1.1, 1.2, 2.1, 2.2, 6.1, 6.2, 7.1, 7.2, 7.3 |
| `/api/poster/quota` | GET | 获取用户剩余配额 | 7.2 |
| `/api/poster/image/{image_id}` | GET | 获取生成的图片 | - |

**请求头参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `X-User-Id` | string | 是 | 用户 ID |
| `X-User-Tier` | string | 否 | 会员等级 (free/basic/professional)，默认 free |

**错误码定义：**

| 错误码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| `INVALID_INPUT` | 400 | 请求参数无效 |
| `CONTENT_BLOCKED` | 400 | 内容包含敏感词 |
| `RATE_LIMIT_EXCEEDED` | 429 | 超出每日生成限额 |
| `TEMPLATE_NOT_FOUND` | 404 | 指定的模板不存在 |
| `IMAGE_NOT_FOUND` | 404 | 图片不存在 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |
| `UNAUTHORIZED` | 401 | 未提供用户认证信息 |

**使用示例：**

```python
import httpx

# 生成海报
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/poster/generate",
        headers={
            "X-User-Id": "user123",
            "X-User-Tier": "basic",
        },
        json={
            "scene_description": "夏日海滩促销场景",
            "marketing_text": "限时特惠 5折起",
            "language": "zh",
            "aspect_ratio": "1:1",
            "batch_size": 1,
        },
    )
    result = response.json()
    print(f"生成了 {len(result['images'])} 张图片")
    # 生成成功后会自动保存历史记录

# 查询剩余配额
async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/api/poster/quota",
        headers={"X-User-Id": "user123", "X-User-Tier": "free"},
    )
    quota = response.json()
    print(f"剩余配额: {quota['remaining_quota']}")
```

**依赖注入设计：**

API 使用 FastAPI 的依赖注入机制实现关注点分离：
- `get_current_user_id()`: 从请求头获取用户 ID
- `get_current_user_tier()`: 从请求头获取会员等级
- `check_rate_limit()`: 检查用户限流状态
- `get_db_session()`: 获取数据库会话（用于历史记录保存）

**生成流程：**

```
1. 认证检查 → 验证用户身份
2. 限流检查 → 检查用户配额
3. 内容过滤 → 检查敏感词
4. 海报生成 → 调用 AI 模型生成图片
5. 增加计数 → 更新用户使用次数
6. 保存历史 → 记录生成信息到数据库（Requirements 6.2）
7. 返回结果 → 返回生成的图片信息
```

**特性：**
- 完整的认证和限流检查
- 敏感内容过滤（在服务层处理）
- 生成成功后才增加使用计数
- 生成成功后自动保存历史记录（Requirements 6.2）
- 历史记录保存失败不影响主流程，自动回滚数据库会话以清除错误状态
- 详细的错误响应，包含错误码和消息

---

### UploadAPI (`app/api/upload.py`)

文件上传 API 模块，处理商品图片上传。

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/upload/product` | POST | 上传商品白底图，返回 Base64 数据 URL |

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `file` | UploadFile | 是 | 商品白底图文件 |

**支持的图片格式：**

| MIME 类型 | 说明 |
|-----------|------|
| `image/png` | PNG 格式 |
| `image/jpeg` | JPEG 格式 |

**响应格式：**

```json
{
  "url": "data:image/png;base64,iVBORw0KGgo..."
}
```

**错误码定义：**

| 错误码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| `INVALID_IMAGE` | 400 | 不支持的图片格式 |

**使用示例：**

```python
import httpx

# 上传商品图片
async with httpx.AsyncClient() as client:
    with open("product.png", "rb") as f:
        response = await client.post(
            "http://localhost:8000/api/upload/product",
            files={"file": ("product.png", f, "image/png")},
        )
    result = response.json()
    print(f"图片 URL: {result['url'][:50]}...")  # Base64 数据 URL
```

**特性：**
- 支持 PNG 和 JPEG 格式
- 返回 Base64 数据 URL，可直接用于场景融合等功能
- 无需认证即可使用

---

### AuthAPI (`app/api/auth.py`)

用户认证 API 模块，提供用户注册、登录、Token 管理和登出功能。

| 端点 | 方法 | 功能 | 相关需求 |
|------|------|------|----------|
| `/api/auth/send-code` | POST | 发送短信验证码 | 1.6 |
| `/api/auth/register/phone` | POST | 手机号注册 | 1.1, 1.2, 1.5 |
| `/api/auth/register/email` | POST | 邮箱注册 | 1.5, 1.7 |
| `/api/auth/login/phone` | POST | 手机号登录 | 2.1 |
| `/api/auth/login/email` | POST | 邮箱登录 | 2.6 |
| `/api/auth/refresh` | POST | 刷新 Token | 2.3, 2.4 |
| `/api/auth/logout` | POST | 登出 | 3.1 |
| `/api/auth/me` | GET | 获取当前用户信息 | 2.5 |

**请求/响应 Schema：**

| Schema | 用途 |
|--------|------|
| `SendCodeRequest` | 发送验证码请求（手机号） |
| `SendCodeResponse` | 发送验证码响应（成功状态、消息、冷却时间） |
| `PhoneRegisterRequest` | 手机号注册请求（手机号、验证码） |
| `EmailRegisterRequest` | 邮箱注册请求（邮箱、密码） |
| `PhoneLoginRequest` | 手机号登录请求（手机号、验证码） |
| `EmailLoginRequest` | 邮箱登录请求（邮箱、密码） |
| `RefreshTokenRequest` | 刷新 Token 请求（refresh_token） |
| `LogoutRequest` | 登出请求（refresh_token） |
| `TokenResponse` | Token 响应（access_token、refresh_token、token_type、expires_in） |
| `UserResponse` | 用户信息响应（id、phone、email、membership_tier、membership_expiry、created_at） |
| `AuthResponse` | 认证响应（包含 user 和 tokens） |
| `MessageResponse` | 通用消息响应（success、message） |

**错误码定义：**

| 错误码 | HTTP 状态码 | 说明 |
|--------|-------------|------|
| `INVALID_PHONE` | 400 | 手机号格式无效 |
| `INVALID_EMAIL` | 400 | 邮箱格式无效 |
| `INVALID_CODE` | 400/401 | 验证码无效或过期 |
| `INVALID_CREDENTIALS` | 401 | 邮箱或密码错误 |
| `PHONE_EXISTS` | 409 | 手机号已注册 |
| `EMAIL_EXISTS` | 409 | 邮箱已注册 |
| `USER_NOT_FOUND` | 401 | 用户不存在 |
| `WEAK_PASSWORD` | 400 | 密码强度不足（少于 8 位） |
| `TOKEN_EXPIRED` | 401 | Token 已过期 |
| `TOKEN_INVALID` | 401 | Token 无效 |
| `TOKEN_REVOKED` | 401 | Token 已被撤销 |
| `RATE_LIMITED` | 429 | 请求过于频繁 |
| `UNAUTHORIZED` | 401 | 未提供认证信息 |

**使用示例：**

```python
import httpx

async with httpx.AsyncClient() as client:
    # 1. 发送验证码
    response = await client.post(
        "http://localhost:8000/api/auth/send-code",
        json={"phone": "13800138000"},
    )
    print(response.json())  # {"success": true, "message": "验证码已发送", "cooldown_remaining": 0}
    
    # 2. 手机号注册
    response = await client.post(
        "http://localhost:8000/api/auth/register/phone",
        json={"phone": "13800138000", "code": "123456"},
    )
    result = response.json()
    access_token = result["tokens"]["access_token"]
    refresh_token = result["tokens"]["refresh_token"]
    print(f"用户 ID: {result['user']['id']}")
    print(f"会员等级: {result['user']['membership_tier']}")  # "free"
    
    # 3. 邮箱注册
    response = await client.post(
        "http://localhost:8000/api/auth/register/email",
        json={"email": "user@example.com", "password": "password123"},
    )
    
    # 4. 获取当前用户信息
    response = await client.get(
        "http://localhost:8000/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    user = response.json()
    print(f"当前用户: {user['email']}")
    
    # 5. 刷新 Token
    response = await client.post(
        "http://localhost:8000/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    new_tokens = response.json()
    print(f"新 Access Token: {new_tokens['access_token'][:20]}...")
    
    # 6. 登出
    response = await client.post(
        "http://localhost:8000/api/auth/logout",
        json={"refresh_token": new_tokens["refresh_token"]},
    )
    print(response.json())  # {"success": true, "message": "登出成功"}
```

**认证依赖：**

| 依赖函数 | 用途 |
|----------|------|
| `get_current_user` | 获取当前认证用户（必须提供有效 Token） |
| `get_optional_current_user` | 获取当前用户（可选，无 Token 时返回 None） |

**特性：**
- 支持手机号 + 验证码和邮箱 + 密码两种注册/登录方式
- JWT Token 认证（Access Token + Refresh Token）
- 新用户默认 FREE 会员等级
- 完整的错误码和错误消息
- 依赖注入设计，便于测试

---

## 核心服务模块

### MembershipService (`app/services/membership_service.py`)

会员权限服务，负责处理会员相关的业务逻辑，包括水印规则判断、功能权限检查和订阅过期管理。

| 方法 | 功能 | 相关需求 |
|------|------|----------|
| `should_add_watermark()` | 判断是否需要添加水印 | 7.1, 7.3 |
| `get_watermark_rule()` | 获取水印规则详情 | 7.1, 7.3 |
| `has_feature_access()` | 检查会员是否有权访问指定功能 | 7.4 |
| `check_feature_access()` | 检查功能访问权限并返回详细结果 | 7.4 |
| `can_access_scene_fusion()` | 检查是否可以访问场景融合功能 | 7.4 |
| `has_priority_processing()` | 检查是否享有优先处理 | 7.3 |
| `get_tier_features()` | 获取指定会员等级可用的所有功能 | 7.1, 7.3, 7.4 |
| `is_subscription_expired()` | 检查用户订阅是否已过期 | 4.7 |
| `check_and_downgrade_if_expired()` | 检查订阅并在过期时自动降级 | 4.7 |
| `downgrade_to_free()` | 将用户降级为 FREE 等级 | 4.7 |
| `check_expired_users()` | 批量检查并降级过期用户 | 4.7 |

**使用示例：**

```python
from app.services.membership_service import MembershipService, get_membership_service, Feature
from app.models.schemas import MembershipTier

# 使用全局单例
service = get_membership_service()

# 检查是否需要添加水印
needs_watermark = service.should_add_watermark(MembershipTier.FREE)  # True
needs_watermark = service.should_add_watermark(MembershipTier.BASIC)  # False

# 获取水印规则详情
rule = service.get_watermark_rule(MembershipTier.FREE)
print(f"添加水印: {rule.should_add_watermark}, 文本: {rule.watermark_text}")

# 检查功能访问权限
can_access = service.has_feature_access(MembershipTier.FREE, Feature.SCENE_FUSION)  # False
can_access = service.has_feature_access(MembershipTier.PROFESSIONAL, Feature.SCENE_FUSION)  # True

# 获取详细的权限检查结果
result = service.check_feature_access(MembershipTier.FREE, Feature.SCENE_FUSION)
if not result.allowed:
    print(f"需要升级: {result.message}")  # "升级到专业会员即可使用场景融合功能"

# 便捷方法
can_fuse = service.can_access_scene_fusion(MembershipTier.PROFESSIONAL)  # True
has_priority = service.has_priority_processing(MembershipTier.BASIC)  # True

# 订阅过期管理
if service.is_subscription_expired(user):
    print("用户订阅已过期")

# 检查并自动降级过期用户
was_downgraded = service.check_and_downgrade_if_expired(user)
if was_downgraded:
    print(f"用户已降级为 FREE: {user.id}")

# 批量检查过期用户（用于定时任务）
downgraded_users = service.check_expired_users(users_list)
print(f"共降级 {len(downgraded_users)} 个用户")
```

**会员功能权限配置：**

| 会员等级 | 可用功能 |
|----------|----------|
| FREE (免费版) | 海报生成、批量生成 |
| BASIC (基础会员) | 海报生成、批量生成、优先处理、无水印 |
| PROFESSIONAL (专业会员) | 海报生成、批量生成、优先处理、无水印、场景融合 |

**特性：**
- 基于会员等级的水印规则判断
- 灵活的功能权限配置
- 提供详细的权限检查结果和升级提示
- 订阅过期自动降级为 FREE 等级
- 支持批量检查过期用户（适用于定时任务）
- 全局单例访问模式

---

### TemplateService (`app/services/template_service.py`)

预设商业模板服务，管理促销类、高级类和节日类模板，支持模板应用和 Prompt 生成。

| 方法 | 功能 | 相关需求 |
|------|------|----------|
| `list_templates()` | 列出所有模板，支持按分类筛选 | 3.1, 3.2, 3.3 |
| `get_template()` | 根据 ID 获取指定模板 | 3.1, 3.2, 3.3 |
| `apply_template()` | 应用模板生成完整 Prompt | 3.4 |
| `get_templates_by_holiday()` | 根据节日类型获取模板 | 3.3 |

**预设模板列表：**

| 分类 | 模板 ID | 名称 | 特点 |
|------|---------|------|------|
| 促销类 | `promo-sale-01` | 限时特惠 | 爆炸贴纸风格、红黄配色、大字号 |
| 促销类 | `promo-flash-02` | 闪购秒杀 | 闪电效果、红橙渐变、紧迫感设计 |
| 促销类 | `promo-discount-03` | 满减优惠 | 优惠券风格、红金配色、层级展示 |
| 高级类 | `premium-minimal-01` | 极简奢华 | 极简留白、黑金配色、优雅排版 |
| 高级类 | `premium-studio-02` | 影棚质感 | 影棚光效、专业摄影风格、聚光灯效果 |
| 高级类 | `premium-blackgold-03` | 黑金尊享 | VIP 专属设计、金色边框、奢华感 |
| 节日类 | `holiday-spring-01` | 春节喜庆 | 中国红、灯笼元素、书法字体 |
| 节日类 | `holiday-valentines-02` | 情人节浪漫 | 粉红配色、爱心元素、浪漫字体 |
| 节日类 | `holiday-double11-03` | 双十一狂欢 | 购物节风格、霓虹效果、倒计时元素 |

**使用示例：**

```python
from app.services.template_service import TemplateService
from app.models.schemas import PosterGenerationRequest, TemplateCategory, HolidayType

service = TemplateService()

# 列出所有模板
all_templates = await service.list_templates()

# 按分类筛选模板
promo_templates = await service.list_templates(category=TemplateCategory.PROMOTIONAL)
premium_templates = await service.list_templates(category=TemplateCategory.PREMIUM)

# 获取指定模板
template = await service.get_template("promo-sale-01")
print(f"模板名称: {template.name}")
print(f"配色方案: {template.prompt_modifiers.color_scheme}")

# 应用模板生成 Prompt
request = PosterGenerationRequest(
    scene_description="夏日清凉饮品促销",
    marketing_text="买一送一",
    language="zh",
    aspect_ratio="1:1",
)
prompt = await service.apply_template("promo-sale-01", request)

# 获取节日模板
spring_templates = await service.get_templates_by_holiday(HolidayType.SPRING_FESTIVAL)
```

**特性：**
- 预设 9 个商业模板，覆盖促销、高级、节日三大场景
- 支持依赖注入 PromptBuilder
- O(1) 时间复杂度的模板 ID 查找
- 返回副本避免外部修改原始数据

---

### SceneFusionService (`app/services/scene_fusion_service.py`)

场景融合服务，将商品白底图与新场景背景融合，生成专业的商品场景图。

| 类/方法 | 功能 | 相关需求 |
|---------|------|----------|
| `ProductExtractor` | 商品主体提取器，从白底图中提取商品 | 4.1 |
| `extract_product()` | 从 URL 加载图像并提取商品主体（支持 http/https 和 data URL） | 4.1 |
| `extract_product_from_bytes()` | 从字节数据提取商品主体 | 4.1 |
| `fuse_with_scene()` | 将商品与场景融合 | 4.2, 4.3 |
| `process_scene_fusion()` | 处理完整的场景融合请求 | 4.1, 4.2, 4.3, 7.4 |
| `process_scene_fusion_with_bytes()` | 处理场景融合并返回图像数据 | 4.1, 4.2, 4.3, 7.4 |

**异常类型：**

| 异常类 | 说明 |
|--------|------|
| `SceneFusionError` | 场景融合错误基类 |
| `ProductExtractionError` | 商品提取错误 |
| `InvalidImageError` | 无效图像错误 |
| `FeatureNotAvailableError` | 功能不可用错误（需要专业会员） |
| `ContentBlockedError` | 内容被阻止错误（敏感词） |

**使用示例：**

```python
from app.services.scene_fusion_service import (
    SceneFusionService,
    ProductExtractor,
    get_scene_fusion_service,
)
from app.models.schemas import SceneFusionRequest, MembershipTier

# 使用全局单例
service = get_scene_fusion_service()

# 方式一：通过 HTTP URL 处理场景融合
request = SceneFusionRequest(
    product_image_url="https://example.com/product.png",
    target_scene="现代简约客厅场景",
    aspect_ratio="1:1",
)
response = await service.process_scene_fusion(
    request,
    user_tier=MembershipTier.PROFESSIONAL,
)
print(f"融合图像 URL: {response.fused_image_url}")
print(f"处理耗时: {response.processing_time_ms}ms")

# 方式二：通过 data URL 处理场景融合（适用于前端直接上传的 Base64 图片）
request = SceneFusionRequest(
    product_image_url="data:image/png;base64,iVBORw0KGgo...",
    target_scene="现代简约客厅场景",
    aspect_ratio="1:1",
)
response = await service.process_scene_fusion(
    request,
    user_tier=MembershipTier.PROFESSIONAL,
)

# 方式三：通过字节数据处理场景融合
with open("product.png", "rb") as f:
    image_data = f.read()

response, fused_image_bytes = await service.process_scene_fusion_with_bytes(
    image_data=image_data,
    target_scene="咖啡厅温馨场景",
    aspect_ratio="16:9",
    user_tier=MembershipTier.PROFESSIONAL,
)

# 单独使用商品提取器
extractor = ProductExtractor()
extracted = extractor.extract(image_data)
print(f"边界框: {extracted.bounding_box}")

# 优化遮罩边缘
refined_mask = extractor.refine_mask(extracted.mask)
```

**ProductExtractor 配置：**

| 常量 | 默认值 | 说明 |
|------|--------|------|
| `WHITE_THRESHOLD` | 240 | 白色背景阈值（RGB 值 ≥ 此值视为白色） |
| `MIN_PRODUCT_RATIO` | 0.01 | 最小商品区域比例（商品至少占图像的 1%） |

**支持的图像 URL 格式：**

| 格式 | 示例 | 说明 |
|------|------|------|
| HTTP/HTTPS URL | `https://example.com/product.png` | 从远程服务器下载图像 |
| Data URL | `data:image/png;base64,iVBORw0KGgo...` | Base64 编码的图像数据，适用于前端直接上传 |

**特性：**
- 基于颜色阈值分割的白底商品提取
- 自动计算商品边界框
- 生成带透明背景的商品图像和遮罩
- 支持遮罩边缘优化（高斯模糊平滑）
- 集成会员权限检查（仅专业会员可用）
- 集成内容安全过滤
- 支持 HTTP/HTTPS URL 和 data URL 两种图像输入方式
- 依赖注入设计，便于测试
- 全局单例访问模式

---

### PosterService (`app/services/poster_service.py`)

海报生成服务，整合 PromptBuilder、ContentFilter、TemplateService、ZImageClient、MembershipService 和 StorageService，实现完整的海报生成流程。

| 方法 | 功能 | 相关需求 |
|------|------|----------|
| `generate_poster()` | 生成海报（完整流程） | 1.1, 1.2, 2.1, 2.2, 5.1, 7.1, 7.3 |
| `generate_poster_with_storage()` | 生成海报并返回图像数据 | 1.1, 1.2, 2.1, 2.2, 7.1, 7.3 |

**内部方法：**

| 方法 | 功能 |
|------|------|
| `_upload_or_fallback()` | 上传图片到 S3，失败时回退到 Base64 |
| `_check_content()` | 检查请求内容是否包含敏感词 |
| `_build_prompt()` | 构建生成 Prompt（支持模板） |

**异常类型：**

| 异常类 | 说明 |
|--------|------|
| `PosterGenerationError` | 海报生成错误基类 |
| `ContentBlockedError` | 内容被阻止错误（包含敏感词） |
| `TemplateNotFoundError` | 模板未找到错误 |

**依赖注入：**

| 依赖 | 说明 |
|------|------|
| `PromptBuilder` | Prompt 构建器 |
| `ContentFilterService` | 内容过滤服务 |
| `TemplateService` | 模板服务 |
| `ZImageTurboClient` | AI 图像生成客户端 |
| `MembershipService` | 会员服务（水印规则） |
| `WatermarkProcessor` | 水印处理器 |
| `StorageService` | 存储服务（S3 上传） |

**使用示例：**

```python
from app.services.poster_service import PosterService, get_poster_service
from app.models.schemas import PosterGenerationRequest, MembershipTier

# 使用全局单例（自动注入 StorageService）
poster_service = get_poster_service()

# 生成海报
request = PosterGenerationRequest(
    scene_description="夏日海滩促销场景",
    marketing_text="限时特惠 5折起",
    language="zh",
    aspect_ratio="1:1",
    batch_size=1,
)

response = await poster_service.generate_poster(
    request=request,
    user_tier=MembershipTier.BASIC,
    user_id="user123",
)

print(f"请求 ID: {response.request_id}")
print(f"处理时间: {response.processing_time_ms}ms")
for image in response.images:
    print(f"图片 URL: {image.url}")
    print(f"缩略图 URL: {image.thumbnail_url}")
    print(f"有水印: {image.has_watermark}")
    # 如果 S3 不可用，image_base64 会包含 Base64 数据
    if image.image_base64:
        print("使用 Base64 回退模式")
```

**生成流程：**

```
1. 内容过滤检查 → 检查场景描述和营销文案是否包含敏感词
2. 构建 Prompt → 应用模板（如果指定）或直接构建
3. 计算图像尺寸 → 根据宽高比计算实际像素尺寸
4. 调用 AI 模型 → 生成单张或批量图像
5. 获取水印规则 → 根据会员等级判断是否添加水印
6. 处理图像 → 添加水印（如需要）
7. 上传到 S3 → 成功返回 CDN URL，失败回退到 Base64
8. 返回结果 → 包含图片 URL、缩略图、水印标记等
```

**S3 存储集成（Requirements 5.1）：**

- 生成的图片会自动上传到 S3 存储
- 如果 S3 配置可用，返回 CDN URL
- 如果 S3 不可用或上传失败，自动回退到 Base64 data URL
- `image_base64` 字段仅在回退模式下有值

**特性：**
- 完整的海报生成流程
- 集成敏感内容过滤
- 支持预设模板应用
- 根据会员等级自动添加水印
- S3 存储集成，支持 CDN URL
- S3 不可用时自动回退到 Base64
- 依赖注入设计，便于测试
- 全局单例访问模式

---

### ContentFilterService (`app/services/content_filter.py`)

敏感内容过滤服务，用于检查用户输入是否包含敏感词。

| 方法 | 功能 | 相关需求 |
|------|------|----------|
| `check_content()` | 检查文本是否包含敏感词 | 6.1 |
| `add_to_blocklist()` | 添加敏感词到黑名单 | 6.1 |
| `remove_from_blocklist()` | 从黑名单移除敏感词 | 6.1 |
| `load_blocklist_from_file()` | 从文件加载敏感词列表 | 6.1 |
| `clear_blocklist()` | 清空敏感词列表 | 6.1 |

**使用示例：**

```python
from app.services.content_filter import ContentFilterService, get_content_filter

# 使用全局单例
filter_service = get_content_filter()
result = filter_service.check_content("这是一段测试文本")

if not result.is_allowed:
    print(f"内容被拦截: {result.warning_message}")
    print(f"敏感词: {result.blocked_keywords}")

# 或创建自定义实例
custom_filter = ContentFilterService(blocklist={"自定义敏感词"})
custom_filter.add_to_blocklist(["新增敏感词1", "新增敏感词2"])
```

**特性：**
- 预编译正则表达式，提高匹配效率
- 支持中英文敏感词
- 大小写不敏感匹配
- 支持从外部文件加载敏感词列表
- 提供全局单例访问模式

---

### StorageService (`app/services/storage_service.py`)

图片存储服务，支持 S3 兼容存储，当 S3 不可用时自动回退到 Base64 编码。

| 方法 | 功能 | 相关需求 |
|------|------|----------|
| `upload_image()` | 上传图片到 S3，同时生成缩略图 | 8.1 |
| `generate_thumbnail()` | 生成缩略图（JPEG 格式） | 8.1 |
| `get_signed_url()` | 获取带过期时间的签名 URL | 8.1 |
| `delete_image()` | 删除 S3 中的图片 | 8.1 |
| `extract_key_from_url()` | 从 URL 中提取 S3 对象键 | 8.1 |
| `is_s3_available` | 检查 S3 是否可用（属性） | 8.1 |

**异常类型：**

| 异常类 | 说明 |
|--------|------|
| `S3StorageError` | S3 存储错误 |

**环境变量配置：**

| 环境变量 | 说明 |
|----------|------|
| `S3_BUCKET` | S3 存储桶名称 |
| `S3_ENDPOINT` | S3 端点 URL（支持 AWS S3 或兼容服务） |
| `S3_ACCESS_KEY` | S3 访问密钥 |
| `S3_SECRET_KEY` | S3 密钥 |
| `S3_REGION` | S3 区域（默认 us-east-1） |
| `S3_PUBLIC_URL` | CDN URL 前缀（可选） |
| `S3_SIGNED_URL_EXPIRES` | 签名 URL 过期时间（秒，默认 3600） |

**使用示例：**

```python
from app.services.storage_service import StorageService, get_storage_service

# 使用全局单例
storage = get_storage_service()

# 检查 S3 是否可用
if storage.is_s3_available:
    print("S3 存储已启用")
else:
    print("使用 Base64 回退模式")

# 上传图片（自动生成缩略图）
with open("product.jpg", "rb") as f:
    image_data = f.read()

original_url, thumbnail_url = await storage.upload_image(
    image_data=image_data,
    user_id="user123",
)
print(f"原图 URL: {original_url}")
print(f"缩略图 URL: {thumbnail_url}")

# 生成签名 URL（带过期时间）
key = storage.extract_key_from_url(original_url)
if key:
    signed_url = storage.get_signed_url(key, expires_in=3600)
    print(f"签名 URL: {signed_url}")

# 删除图片
if key:
    success = await storage.delete_image(key)
    print(f"删除结果: {success}")

# 单独生成缩略图
thumbnail_data = storage.generate_thumbnail(
    image_data=image_data,
    max_size=(200, 200),
)
```

**S3 对象键格式：**

```
images/{user_id}/{YYYY}/{MM}/{DD}/{uuid}.jpg
images/{user_id}/{YYYY}/{MM}/{DD}/{uuid}_thumb.jpg
```

**特性：**
- 支持 AWS S3 及兼容服务（如 MinIO、阿里云 OSS 等）
- S3 不可用时自动回退到 Base64 data URL
- 自动生成缩略图（200x200，JPEG 格式，保持宽高比）
- 支持 CDN URL 配置
- 支持签名 URL（带过期时间）
- 全局单例访问模式
- 异步上传和删除操作

**SDK 依赖：**

| SDK | 版本 | 用途 |
|-----|------|------|
| `boto3` | >=1.28.0 | AWS S3 SDK |

---

### AuthService (`app/services/auth_service.py`)

用户认证服务，负责处理用户注册、登录、Token 管理和登出功能。

| 方法 | 功能 | 相关需求 |
|------|------|----------|
| `register_with_phone()` | 手机号 + 验证码注册 | 1.1, 1.2, 1.5 |
| `register_with_email()` | 邮箱 + 密码注册 | 1.5, 1.7 |
| `login_with_phone()` | 手机号 + 验证码登录 | 2.1 |
| `login_with_email()` | 邮箱 + 密码登录 | 2.6 |
| `refresh_token()` | 刷新 Access Token | 2.3, 2.4 |
| `logout()` | 登出（使 Refresh Token 失效） | 3.1 |
| `send_verification_code()` | 发送短信验证码 | 1.6 |
| `get_current_user()` | 从 Access Token 获取当前用户 | 2.5 |

**异常类型：**

| 异常类 | 说明 |
|--------|------|
| `AuthError` | 认证错误基类 |
| `PhoneAlreadyExistsError` | 手机号已注册 |
| `EmailAlreadyExistsError` | 邮箱已注册 |
| `InvalidPhoneFormatError` | 手机号格式无效 |
| `InvalidEmailFormatError` | 邮箱格式无效 |
| `InvalidVerificationCodeError` | 验证码无效或过期 |
| `InvalidCredentialsError` | 登录凭证无效 |
| `UserNotFoundError` | 用户不存在 |
| `TokenRevokedError` | Token 已被撤销 |
| `WeakPasswordError` | 密码强度不足 |

**使用示例：**

```python
from app.services.auth_service import AuthService, get_auth_service
from app.services.sms_service import SMSService

# 使用全局单例
auth_service = get_auth_service()

# 手机号注册
await auth_service.send_verification_code("13800138000")
result = await auth_service.register_with_phone("13800138000", "123456")
print(f"用户 ID: {result.user.id}")
print(f"Access Token: {result.tokens.access_token}")

# 邮箱注册
result = await auth_service.register_with_email("user@example.com", "password123")

# 手机号登录
result = await auth_service.login_with_phone("13800138000", "123456")

# 邮箱登录
result = await auth_service.login_with_email("user@example.com", "password123")

# 刷新 Token
new_tokens = await auth_service.refresh_token(result.tokens.refresh_token)

# 登出
await auth_service.logout(result.tokens.refresh_token)

# 获取当前用户
user = auth_service.get_current_user(access_token)
```

**验证规则：**

| 字段 | 规则 |
|------|------|
| 手机号 | 中国大陆手机号格式 (`1[3-9]\d{9}`) |
| 邮箱 | 标准邮箱格式 |
| 密码 | 最少 8 个字符 |

**特性：**
- 使用 bcrypt 进行密码哈希
- 支持手机号和邮箱两种注册/登录方式
- Token 刷新时自动撤销旧 Token
- 依赖注入设计，便于测试
- 全局单例访问模式
- 新用户默认 FREE 会员等级

---

### SMSService (`app/services/sms_service.py`)

短信验证码服务，负责验证码的生成、存储、验证和发送频率限制。

| 方法 | 功能 | 相关需求 |
|------|------|----------|
| `send_code()` | 发送验证码 | 1.6 |
| `verify_code()` | 验证验证码 | 1.3 |
| `is_rate_limited()` | 检查是否在冷却期 | 1.6 |
| `get_cooldown_remaining()` | 获取剩余冷却时间 | 1.6 |

**支持的短信服务商：**

| 服务商 | 类名 | 说明 |
|--------|------|------|
| Mock | `MockSMSProvider` | 模拟服务商（开发测试用） |
| 阿里云 | `AliyunSMSProvider` | 阿里云短信服务 |
| 腾讯云 | `TencentSMSProvider` | 腾讯云短信服务 |

**配置参数：**

| 常量 | 默认值 | 说明 |
|------|--------|------|
| `CODE_LENGTH` | 6 | 验证码长度 |
| `CODE_EXPIRY_MINUTES` | 5 | 验证码有效期（分钟） |
| `RATE_LIMIT_SECONDS` | 60 | 发送频率限制（秒） |

**环境变量配置（阿里云）：**

| 环境变量 | 说明 |
|----------|------|
| `ALIYUN_ACCESS_KEY_ID` | 阿里云 AccessKey ID |
| `ALIYUN_ACCESS_KEY_SECRET` | 阿里云 AccessKey Secret |
| `ALIYUN_SMS_SIGN_NAME` | 短信签名 |
| `ALIYUN_SMS_TEMPLATE_CODE` | 短信模板 ID |

**环境变量配置（腾讯云）：**

| 环境变量 | 说明 |
|----------|------|
| `TENCENT_SECRET_ID` | 腾讯云 SecretId |
| `TENCENT_SECRET_KEY` | 腾讯云 SecretKey |
| `TENCENT_SMS_APP_ID` | 短信应用 ID |
| `TENCENT_SMS_SIGN_NAME` | 短信签名 |
| `TENCENT_SMS_TEMPLATE_ID` | 短信模板 ID |

**使用示例：**

```python
from app.services.sms_service import SMSService, get_sms_service

# 使用全局单例
sms_service = get_sms_service()

# 发送验证码
result = await sms_service.send_code("13800138000")
if result.success:
    print("验证码已发送")
else:
    print(f"发送失败: {result.message}")
    print(f"剩余冷却时间: {result.cooldown_remaining}秒")

# 验证验证码
verify_result = sms_service.verify_code("13800138000", "123456")
if verify_result.success:
    print("验证成功")
else:
    print(f"验证失败: {verify_result.message}")

# 检查频率限制
if sms_service.is_rate_limited("13800138000"):
    remaining = sms_service.get_cooldown_remaining("13800138000")
    print(f"请等待 {remaining} 秒后重试")
```

**特性：**
- 6 位数字验证码
- 5 分钟有效期
- 60 秒发送频率限制
- 支持阿里云和腾讯云短信服务
- 验证码使用后自动失效
- 全局单例访问模式

---

### PaymentService (`app/services/payment_service.py`)

支付订阅服务，负责处理订阅计划管理、订单创建、支付状态管理和会员升级功能。

| 方法 | 功能 | 相关需求 |
|------|------|----------|
| `get_all_plans()` | 获取所有订阅计划 | 4.1 |
| `get_plan_info()` | 获取指定计划详情 | 4.1 |
| `get_plan_price()` | 获取计划价格 | 4.1 |
| `get_plan_tier()` | 获取计划对应的会员等级 | 4.1 |
| `get_plan_duration()` | 获取计划有效期（天数） | 4.1 |
| `create_order()` | 创建支付订单 | 4.1 |
| `get_order()` | 获取订单信息 | 4.9 |
| `get_order_status()` | 获取订单状态 | 4.9 |
| `get_user_orders()` | 获取用户所有订单 | 4.9 |
| `is_order_expired()` | 检查订单是否过期 | 4.9 |
| `mark_order_paid()` | 标记订单为已支付 | 4.5 |
| `mark_order_failed()` | 标记订单为失败 | 4.6 |
| `upgrade_user_membership()` | 升级用户会员等级 | 4.5 |
| `calculate_membership_expiry()` | 计算会员过期时间 | 4.5 |
| `process_payment_success()` | 处理支付成功回调 | 4.5 |
| `process_payment_failure()` | 处理支付失败回调 | 4.6 |

**订阅计划配置：**

| 计划 | 名称 | 价格 | 会员等级 | 有效期 |
|------|------|------|----------|--------|
| `BASIC_MONTHLY` | 基础会员月付 | 29 元 | BASIC | 30 天 |
| `BASIC_YEARLY` | 基础会员年付 | 299 元 | BASIC | 365 天 |
| `PRO_MONTHLY` | 专业会员月付 | 99 元 | PROFESSIONAL | 30 天 |
| `PRO_YEARLY` | 专业会员年付 | 999 元 | PROFESSIONAL | 365 天 |

**异常类型：**

| 异常类 | 说明 |
|--------|------|
| `PaymentError` | 支付错误基类 |
| `OrderNotFoundError` | 订单不存在 |
| `OrderExpiredError` | 订单已过期 |
| `InvalidOrderStatusError` | 订单状态转换无效 |
| `UserNotFoundError` | 用户不存在 |

**数据类：**

| 数据类 | 说明 |
|--------|------|
| `PlanInfo` | 订阅计划信息（计划、名称、价格、等级、有效期、描述） |
| `OrderResult` | 订单创建结果（订单、支付 URL、二维码 URL） |

**配置参数：**

| 常量 | 默认值 | 说明 |
|------|--------|------|
| `ORDER_EXPIRY_MINUTES` | 30 | 订单过期时间（分钟） |

**使用示例：**

```python
from app.services.payment_service import PaymentService, get_payment_service
from app.models.schemas import SubscriptionPlan, PaymentMethod, MembershipTier

# 使用全局单例
payment_service = get_payment_service()

# 获取所有订阅计划
plans = payment_service.get_all_plans()
for plan in plans:
    print(f"{plan.name}: {plan.price / 100}元/{plan.duration_days}天")

# 获取指定计划信息
plan_info = payment_service.get_plan_info(SubscriptionPlan.PRO_MONTHLY)
print(f"计划: {plan_info.name}")
print(f"价格: {plan_info.price / 100}元")
print(f"等级: {plan_info.tier.value}")
print(f"描述: {plan_info.description}")

# 创建支付订单
order = payment_service.create_order(
    user_id="user123",
    plan=SubscriptionPlan.PRO_MONTHLY,
    method=PaymentMethod.ALIPAY,
)
print(f"订单 ID: {order.id}")
print(f"金额: {order.amount / 100}元")
print(f"状态: {order.status.value}")

# 查询订单状态
status = payment_service.get_order_status(order.id)
print(f"当前状态: {status.value}")

# 获取用户所有订单
user_orders = payment_service.get_user_orders("user123")
print(f"用户共有 {len(user_orders)} 个订单")

# 处理支付成功（模拟支付回调）
from app.models.database import User
user = User(id="user123", membership_tier=MembershipTier.FREE, ...)
paid_order = payment_service.process_payment_success(
    order_id=order.id,
    external_order_id="alipay_order_123",
    user=user,
)
print(f"订单已支付: {paid_order.status.value}")
print(f"用户会员等级: {user.membership_tier.value}")
print(f"会员过期时间: {user.membership_expiry}")

# 计算会员过期时间（支持续费叠加）
new_expiry = payment_service.calculate_membership_expiry(
    plan=SubscriptionPlan.PRO_YEARLY,
    current_expiry=user.membership_expiry,  # 如果有现有会员，从过期时间开始叠加
)
print(f"新过期时间: {new_expiry}")
```

**特性：**
- 支持 4 种订阅计划（基础/专业 × 月付/年付）
- 订单 30 分钟过期自动失效
- 支付成功后自动升级会员等级
- 会员续费时间叠加（从当前过期时间开始计算）
- 支持支付宝、微信、银联三种支付方式
- 全局单例访问模式
- 依赖注入设计，便于测试

**支付 SDK 依赖：**

| SDK | 版本 | 用途 |
|-----|------|------|
| `alipay-sdk-python` | >=3.6.0 | 支付宝支付集成 |
| `wechatpayv3` | >=1.2.0 | 微信支付 V3 API 集成 |

---

### HistoryService (`app/services/history_service.py`)

生成历史记录服务，负责管理用户的图像生成历史，包括记录创建、查询、删除和过期清理。

| 方法 | 功能 | 相关需求 |
|------|------|----------|
| `get_user_history()` | 获取用户分页历史记录列表 | 6.1 |
| `get_record_detail()` | 获取单条记录详情 | 6.3 |
| `delete_record()` | 删除历史记录 | 6.4 |
| `create_record()` | 创建新的生成记录 | - |
| `cleanup_expired_records()` | 清理过期记录 | 6.5, 6.6 |
| `get_retention_days()` | 获取会员等级对应的保留天数 | 6.5, 6.6 |
| `is_record_expired()` | 检查记录是否已过期 | 6.5, 6.6 |

**历史记录保留策略：**

| 会员等级 | 保留天数 | 说明 |
|----------|----------|------|
| FREE | 7 天 | 免费用户历史记录保留 7 天 |
| BASIC | 90 天 | 基础会员历史记录保留 90 天 |
| PROFESSIONAL | 90 天 | 专业会员历史记录保留 90 天 |

**使用示例：**

```python
from app.services.history_service import HistoryService
from app.models.schemas import GenerationType, MembershipTier
from sqlalchemy.ext.asyncio import AsyncSession

# 创建服务实例（需要数据库会话）
async def example(db: AsyncSession):
    service = HistoryService(db)
    
    # 获取用户分页历史记录
    records, total = await service.get_user_history(
        user_id="user123",
        page=1,
        page_size=20,
    )
    print(f"共 {total} 条记录，当前页 {len(records)} 条")
    
    # 获取单条记录详情
    record = await service.get_record_detail(
        record_id="record123",
        user_id="user123",
    )
    if record:
        print(f"记录类型: {record.type.value}")
        print(f"处理时间: {record.processing_time_ms}ms")
    
    # 创建新的生成记录
    new_record = await service.create_record(
        user_id="user123",
        generation_type=GenerationType.POSTER,
        input_params={"scene": "夏日海滩", "text": "限时特惠"},
        output_urls=["https://cdn.example.com/image1.jpg"],
        processing_time_ms=1500,
        has_watermark=False,
    )
    print(f"创建记录: {new_record.id}")
    
    # 删除历史记录
    deleted = await service.delete_record(
        record_id="record123",
        user_id="user123",
    )
    print(f"删除结果: {deleted}")
    
    # 清理过期记录（定时任务使用）
    deleted_count = await service.cleanup_expired_records()
    print(f"清理了 {deleted_count} 条过期记录")
    
    # 检查记录是否过期
    from datetime import datetime
    is_expired = service.is_record_expired(
        record_created_at=datetime(2025, 1, 1),
        membership_tier=MembershipTier.FREE,
    )
    print(f"记录是否过期: {is_expired}")
    
    # 获取会员等级对应的保留天数
    retention = service.get_retention_days(MembershipTier.FREE)
    print(f"FREE 用户保留天数: {retention}")  # 7
```

**特性：**
- 分页查询支持，按创建时间倒序排列
- 用户授权检查，只能访问自己的记录
- 级联删除关联的图片记录
- 基于会员等级的差异化保留策略
- 支持批量清理过期记录（适用于定时任务）
- 依赖注入数据库会话，便于测试

---

## 后台任务模块

### TasksModule (`app/tasks/`)

后台定时任务模块，负责执行周期性的系统维护任务。

**模块结构：**

| 文件 | 说明 |
|------|------|
| `__init__.py` | 模块导出，提供公共 API |
| `scheduler.py` | 任务调度器，包含具体任务实现 |

**导出的函数：**

| 函数 | 功能 | 相关需求 |
|------|------|----------|
| `run_subscription_expiry_check()` | 检查并降级过期订阅用户 | 4.7 |
| `run_history_cleanup()` | 清理过期的历史记录 | 6.5, 6.6 |
| `start_scheduler()` | 启动后台任务调度器 | - |
| `stop_scheduler()` | 停止后台任务调度器 | - |

**任务执行间隔：**

| 任务 | 间隔 | 说明 |
|------|------|------|
| 订阅过期检查 | 1 小时 | 检查付费会员是否过期，过期则降级为 FREE |
| 历史记录清理 | 24 小时 | 根据会员等级清理过期的生成记录 |

**使用示例：**

```python
from app.tasks import (
    run_subscription_expiry_check,
    run_history_cleanup,
    start_scheduler,
    stop_scheduler,
)

# 在应用启动时启动调度器
@app.on_event("startup")
async def startup():
    await start_scheduler()

# 在应用关闭时停止调度器
@app.on_event("shutdown")
async def shutdown():
    await stop_scheduler()

# 手动执行任务（用于测试或一次性运行）
async def manual_tasks():
    # 检查订阅过期
    downgraded_count = await run_subscription_expiry_check()
    print(f"降级了 {downgraded_count} 个过期用户")
    
    # 清理历史记录
    cleaned_count = await run_history_cleanup()
    print(f"清理了 {cleaned_count} 条过期记录")
```

**CLI 手动执行：**

```bash
# 运行订阅过期检查
python -m app.tasks.scheduler --task expiry

# 运行历史记录清理
python -m app.tasks.scheduler --task cleanup

# 运行所有任务
python -m app.tasks.scheduler --task all
```

**环境变量配置：**

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `ENABLE_SCHEDULER` | 是否启用后台调度器 | `false` |

**特性：**
- 异步任务执行，不阻塞主应用
- 支持通过环境变量启用/禁用调度器
- 提供 CLI 入口用于手动执行任务
- 优雅的启动/停止机制
- 完整的日志记录

**需求追溯：**
- Requirements 4.7: 订阅过期自动降级为 FREE
- Requirements 6.5: FREE 用户历史记录保留 7 天
- Requirements 6.6: BASIC/PROFESSIONAL 用户历史记录保留 90 天

---

## 外部服务 SDK 依赖汇总

| SDK | 版本 | 用途 |
|-----|------|------|
| `boto3` | >=1.28.0 | AWS S3 存储（图片上传、缩略图、签名 URL） |
| `alipay-sdk-python` | >=3.6.0 | 支付宝支付集成 |
| `wechatpayv3` | >=1.2.0 | 微信支付 V3 API 集成 |

---

## 外部服务客户端

### ZImageTurboClient (`app/clients/zimage_client.py`)

Z-Image-Turbo AI 模型客户端，通过 ModelScope 异步 API 进行图像生成，支持单张生成、批量生成功能。

| 类/函数 | 功能 | 相关需求 |
|---------|------|----------|
| `AspectRatioCalculator` | 图像尺寸计算器，根据宽高比计算实际像素尺寸 | 5.1, 5.2, 5.3 |
| `ZImageTurboClient` | ModelScope AI 模型客户端，支持图像生成 | 2.1, 2.2 |
| `calculate_image_dimensions()` | 便捷函数：计算图像尺寸 | 5.1, 5.2, 5.3 |
| `validate_image_dimensions()` | 便捷函数：验证图像尺寸是否符合宽高比 | 5.1, 5.2, 5.3 |

**ZImageTurboClient 方法：**

| 方法 | 功能 | 相关需求 |
|------|------|----------|
| `generate_image()` | 生成单张图像（异步任务模式） | 2.1 |
| `generate_batch()` | 批量生成图像（预览模式） | 2.2 |
| `image_to_image()` | 图生图（当前通过文生图实现） | 4.1, 4.2, 4.3 |

**内部方法（异步任务处理）：**

| 方法 | 功能 |
|------|------|
| `_submit_task()` | 提交生成任务到 ModelScope，返回 task_id |
| `_poll_task()` | 轮询任务状态，等待完成后返回图像数据 |
| `_get_headers()` | 获取 API 请求头（支持异步模式） |
| `_get_task_headers()` | 获取任务查询请求头 |

**支持的宽高比：**

| 宽高比 | 用途 | 默认尺寸 (base_size=1024) |
|--------|------|---------------------------|
| `1:1` | 正方形，适合微信朋友圈 | 1024 × 1024 |
| `9:16` | 手机海报，适合手机屏幕 | 576 × 1024 |
| `16:9` | 视频封面，适合视频缩略图 | 1024 × 576 |

**配置参数：**

| 参数 | 环境变量 | 默认值 | 说明 |
|------|----------|--------|------|
| `api_key` | `MODELSCOPE_API_KEY` | - | ModelScope API 密钥 |
| `base_url` | `MODELSCOPE_BASE_URL` | `https://api-inference.modelscope.cn/` | API 基础地址 |
| `timeout_ms` | `ZIMAGE_TIMEOUT` | `30000` | 超时时间（毫秒） |
| `poll_interval` | - | `1.0` | 任务轮询间隔（秒） |

**使用示例：**

```python
from app.clients.zimage_client import (
    ZImageTurboClient,
    AspectRatioCalculator,
    calculate_image_dimensions,
    validate_image_dimensions,
)
from app.models.schemas import GenerationOptions

# 计算图像尺寸
width, height = calculate_image_dimensions("9:16")  # (576, 1024)
width, height = calculate_image_dimensions("1:1", base_size=512)  # (512, 512)

# 验证图像尺寸
is_valid = validate_image_dimensions(1024, 1024, "1:1")  # True
is_valid = validate_image_dimensions(1920, 1080, "16:9")  # True

# 创建客户端（使用环境变量配置）
client = ZImageTurboClient()

# 或自定义配置
client = ZImageTurboClient(
    api_key="your-api-key",
    base_url="https://api-inference.modelscope.cn/",
    timeout_ms=30000,
    poll_interval=1.0,
)

# 生成单张图像
options = GenerationOptions(width=1024, height=1024, seed=42)
result = await client.generate_image("夏日海滩促销海报", options)
print(f"生成耗时: {result.generation_time_ms}ms")
print(f"模型版本: {result.model_version}")  # Tongyi-MAI/Z-Image-Turbo

# 批量生成 4 张变体图（预览模式）
results = await client.generate_batch("限时特惠海报", count=4, options=options)
print(f"生成了 {len(results)} 张图像")

# 图生图（当前通过文生图实现，source_image 参数暂不使用）
result = await client.image_to_image(b"", "咖啡厅场景", options)
```

**特性：**
- 使用 ModelScope 异步 API（任务提交 + 轮询模式）
- 支持三种标准宽高比 (1:1, 9:16, 16:9)
- 批量生成使用串行执行，每张图片之间有 2 秒延迟，避免 API 限流
- 每张变体图使用不同的随机种子
- 精确的生成时间统计 (使用 `time.perf_counter()`)
- 自动超时处理和错误重试
- 模型版本：`Tongyi-MAI/Z-Image-Turbo`

**API 工作流程：**

```
1. 提交任务 → POST /v1/images/generations (X-ModelScope-Async-Mode: true)
2. 获取 task_id
3. 轮询状态 → GET /v1/tasks/{task_id}
4. 状态为 SUCCEED 时下载图像
5. 状态为 FAILED 时抛出异常
```

---

## 核心工具模块

### JWTService (`app/utils/jwt.py`)

JWT Token 服务，负责 Access Token 和 Refresh Token 的生成、验证和刷新。

| 方法 | 功能 | 相关需求 |
|------|------|----------|
| `create_access_token()` | 创建 Access Token | 2.1 |
| `create_refresh_token()` | 创建 Refresh Token | 2.1 |
| `create_token_pair()` | 创建 Token 对 | 2.1 |
| `verify_access_token()` | 验证 Access Token | 2.5 |
| `verify_refresh_token()` | 验证 Refresh Token | 2.3 |
| `refresh_tokens()` | 刷新 Token 对 | 2.3 |
| `hash_token()` | 哈希 Token（用于存储） | 2.1 |
| `get_token_expiry()` | 获取 Token 过期时间 | 2.3 |

**配置参数：**

| 参数 | 环境变量 | 默认值 | 说明 |
|------|----------|--------|------|
| `secret_key` | `JWT_SECRET_KEY` | - | JWT 签名密钥 |
| `algorithm` | `JWT_ALGORITHM` | `HS256` | JWT 算法 |
| `access_token_expire_minutes` | `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Access Token 有效期（分钟） |
| `refresh_token_expire_days` | `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh Token 有效期（天） |

**异常类型：**

| 异常类 | 说明 |
|--------|------|
| `JWTError` | JWT 错误基类 |
| `TokenExpiredError` | Token 已过期 |
| `InvalidTokenError` | Token 无效 |

**使用示例：**

```python
from app.utils.jwt import JWTService, get_jwt_service

# 使用全局单例
jwt_service = get_jwt_service()

# 创建 Token 对
tokens = jwt_service.create_token_pair(user_id="user123")
print(f"Access Token: {tokens.access_token}")
print(f"Refresh Token: {tokens.refresh_token}")

# 验证 Access Token
payload = jwt_service.verify_access_token(tokens.access_token)
print(f"User ID: {payload.user_id}")

# 刷新 Token
new_tokens = jwt_service.refresh_tokens(tokens.refresh_token)
```

**特性：**
- 支持 Access Token 和 Refresh Token 分离
- Refresh Token 支持 "记住我" 模式（30 天有效期）
- Token 使用 SHA-256 哈希后存储
- 全局单例访问模式

---

### PromptBuilder (`app/utils/prompt_builder.py`)

用于构建 Z-Image-Turbo 模型的 Prompt，支持：

| 方法 | 功能 | 相关需求 |
|------|------|----------|
| `build_poster_prompt()` | 构建完整的海报生成 Prompt | 1.1, 1.2, 1.4, 1.5 |
| `inject_text_placement()` | 注入中英文文本渲染指令 | 1.1, 1.2, 1.4 |
| `apply_modifiers()` | 应用模板修饰参数 | 3.1, 3.2, 3.3, 3.4 |
| `build_scene_fusion_prompt()` | 构建场景融合 Prompt | 4.1, 4.2, 4.3 |

**使用示例：**

```python
from app.utils.prompt_builder import PromptBuilder
from app.models.schemas import PosterGenerationRequest, PromptModifiers

builder = PromptBuilder()

# 基础海报生成
request = PosterGenerationRequest(
    scene_description="夏日海滩度假场景",
    marketing_text="限时特惠 5折起",
    language="zh",
    aspect_ratio="1:1",
)
prompt = builder.build_poster_prompt(request)

# 带模板修饰的海报生成
modifiers = PromptModifiers(
    style_keywords=["爆炸贴纸", "促销风格"],
    color_scheme="红色背景",
    layout_hints="大字号居中",
    font_style="粗体",
)
prompt_with_template = builder.build_poster_prompt(request, modifiers)
```

---

## 属性测试

项目使用 [Hypothesis](https://hypothesis.readthedocs.io/) 进行属性测试，验证系统在所有有效输入上的正确性。

### 测试文件

| 文件 | 覆盖属性 | 说明 |
|------|----------|------|
| `tests/property/test_prompt_builder_props.py` | Property 1, 4, 5 | PromptBuilder 属性测试 |
| `tests/property/test_zimage_client_props.py` | Property 3, 6 | ZImageTurboClient 批量生成和尺寸计算属性测试 |
| `tests/property/test_content_filter_props.py` | Property 7 | ContentFilterService 属性测试 |
| `tests/property/test_membership_props.py` | Property 8, 10 | MembershipService 水印规则和功能权限属性测试 |
| `tests/property/test_rate_limiter_props.py` | Property 9 | RateLimiter 属性测试 |
| `tests/property/test_auth_props.py` | Property 1, 3, 4, 5 | AuthService 认证属性测试 |
| `tests/property/test_sms_props.py` | Property 2 | SMSService 验证码频率限制属性测试 |

### 已实现的属性测试

#### Property 1: 文本渲染正确性

验证 PromptBuilder 正确嵌入用户提供的营销文案，不做任何修改。

| 测试函数 | 验证内容 | 对应需求 |
|----------|----------|----------|
| `test_chinese_text_preserved_in_prompt` | 中文文案完整保留 | 1.1 |
| `test_english_text_preserved_in_prompt` | 英文文案完整保留 | 1.2 |
| `test_inject_text_placement_preserves_text` | 文本注入方法保留原文 | 1.1, 1.2 |

#### Property 4: 模板参数应用正确性

验证模板参数（风格关键词、配色方案、排版提示、字体风格）正确应用到生成的 Prompt 中。

| 测试函数 | 验证内容 | 对应需求 |
|----------|----------|----------|
| `test_apply_modifiers_contains_all_style_keywords` | 所有风格关键词出现在结果中 | 3.1, 3.2, 3.3 |
| `test_apply_modifiers_contains_color_scheme` | 配色方案出现在结果中 | 3.1, 3.2, 3.3 |
| `test_apply_modifiers_contains_layout_hints` | 排版提示出现在结果中 | 3.1, 3.2, 3.3 |
| `test_apply_modifiers_contains_font_style` | 字体风格出现在结果中 | 3.1, 3.2, 3.3 |
| `test_build_poster_prompt_with_modifiers_contains_all_params` | 完整 Prompt 包含所有模板参数 | 3.1, 3.2, 3.3 |

#### Property 5: 模板与用户输入组合完整性

验证当使用模板生成海报时，最终 Prompt 同时包含模板参数和用户输入内容。

| 测试函数 | 验证内容 | 对应需求 |
|----------|----------|----------|
| `test_template_and_user_input_both_present_in_prompt` | 模板参数与用户输入（场景描述、营销文案）同时出现在最终 Prompt 中 | 3.4 |

#### Property 7: 敏感词过滤有效性

验证 ContentFilterService 正确识别和阻止包含敏感词的内容。

| 测试函数 | 验证内容 | 对应需求 |
|----------|----------|----------|
| `test_content_with_blocklist_keyword_is_rejected` | 包含敏感词的内容被拒绝 | 6.1 |
| `test_blocked_keywords_array_contains_matched_keyword` | 被阻止的关键词数组包含匹配的关键词 | 6.1 |
| `test_content_without_blocklist_keywords_is_allowed` | 不包含敏感词的内容被允许 | 6.1 |
| `test_allowed_content_has_empty_blocked_keywords` | 允许的内容有空的 blocked_keywords | 6.1 |
| `test_multiple_blocklist_keywords_all_detected` | 多个敏感词全部被检测 | 6.1 |
| `test_case_insensitive_matching` | 大小写不敏感匹配 | 6.1 |

#### Property 8: 会员等级水印规则

验证 MembershipService 正确应用基于会员等级的水印规则。

| 测试函数 | 验证内容 | 对应需求 |
|----------|----------|----------|
| `test_free_tier_always_has_watermark` | 免费用户始终添加水印 | 7.1, 7.3 |
| `test_basic_tier_no_watermark` | 基础会员无水印 | 7.1, 7.3 |
| `test_professional_tier_no_watermark` | 专业会员无水印 | 7.1, 7.3 |
| `test_watermark_rule_consistency` | 水印规则一致性验证 | 7.1, 7.3 |
| `test_get_watermark_rule_returns_correct_structure` | WatermarkRule 结构正确性 | 7.1, 7.3 |
| `test_free_tier_watermark_rule_has_text` | 免费用户水印规则包含文本和透明度 | 7.1, 7.3 |
| `test_paid_tier_watermark_rule_no_text` | 付费会员水印规则无文本 | 7.1, 7.3 |
| `test_watermark_rule_idempotent` | 水印规则幂等性验证 | 7.1, 7.3 |

**测试设计亮点：**

- 全面覆盖三种会员等级（FREE/BASIC/PROFESSIONAL）的水印行为
- 验证 `should_add_watermark()` 和 `get_watermark_rule()` 方法的一致性
- 包含幂等性测试，确保多次调用返回相同结果
- 验证 `WatermarkRule` 数据结构的完整性

#### Property 3: 批量生成数量一致性

验证 ZImageTurboClient 的批量生成功能返回正确数量的图像，特别是预览模式（batch_size=4）。

| 测试函数 | 验证内容 | 对应需求 |
|----------|----------|----------|
| `test_batch_generation_returns_exact_count` | 批量生成返回精确数量的图像 | 2.2 |
| `test_preview_mode_returns_exactly_four_images` | 预览模式返回恰好 4 张图像 | 2.2 |
| `test_batch_generation_returns_unique_variants` | 批量生成的每张图像使用不同的种子 | 2.2 |
| `test_batch_generation_with_zero_count_returns_empty_list` | count=0 时返回空列表（边界情况） | 2.2 |

**测试设计亮点：**

- 使用 `unittest.mock.patch` 模拟 AI 模型调用，无需实际 API 依赖
- 验证预览模式（batch_size=4）的特定场景，符合 Requirements 2.2
- 包含变体唯一性验证，确保每张图像使用不同的随机种子
- 覆盖边界情况（count=0）

#### Property 6: 输出尺寸正确性

验证 AspectRatioCalculator 正确计算图像尺寸，确保输出尺寸符合请求的宽高比。

| 测试函数 | 验证内容 | 对应需求 |
|----------|----------|----------|
| `test_square_ratio_produces_equal_dimensions` | 1:1 比例生成相等的宽高 | 5.1 |
| `test_mobile_poster_ratio_produces_correct_proportions` | 9:16 比例生成正确的手机海报尺寸 | 5.2 |
| `test_video_cover_ratio_produces_correct_proportions` | 16:9 比例生成正确的视频封面尺寸 | 5.3 |
| `test_calculated_dimensions_pass_validation` | 计算结果通过验证函数（round-trip 一致性） | 5.1, 5.2, 5.3 |
| `test_dimensions_are_positive_integers` | 生成的尺寸为正整数 | 5.1, 5.2, 5.3 |
| `test_max_dimension_equals_base_size` | 最大维度等于 base_size 参数 | 5.1, 5.2, 5.3 |
| `test_default_base_size_produces_valid_dimensions` | 默认 base_size (1024) 生成有效尺寸 | 5.1, 5.2, 5.3 |

**测试设计亮点：**

- 覆盖三种标准宽高比 (1:1, 9:16, 16:9) 的尺寸计算
- 包含 round-trip 一致性测试，验证计算结果能通过验证函数
- 使用 base_size 范围 (256-2048) 覆盖常见的 AI 图像生成尺寸
- 验证整数舍入的容差处理（±1px tolerance）

#### Property 9: 免费用户每日限额

验证 RateLimiter 正确执行免费用户的每日生成限额（5 次/天）。

| 测试函数 | 验证内容 | 对应需求 |
|----------|----------|----------|
| `test_free_user_blocked_after_limit_reached` | 免费用户达到限额后被阻止 | 7.2 |
| `test_free_user_allowed_before_limit` | 免费用户未达限额时允许 | 7.2 |
| `test_free_user_remaining_quota_correct` | 剩余配额计算正确 | 7.2 |
| `test_free_user_zero_quota_when_exceeded` | 超出限额时配额为 0 | 7.2 |
| `test_free_user_boundary_at_exactly_five` | 边界条件测试（恰好等于 5） | 7.2 |
| `test_basic_member_higher_limit` | 基础会员更高限额（100 次/天） | 7.2 |
| `test_professional_member_unlimited` | 专业会员无限制 | 7.2 |
| `test_sequential_requests_respect_limit` | 顺序请求模拟 | 7.2 |

**测试设计亮点：**

- 采用**纯函数提取**设计模式，将核心业务逻辑从 `RateLimiter.check_limit()` 中提取为 `check_limit_pure()` 纯函数
- 无需 Redis 依赖即可进行属性测试，提高测试速度和可靠性
- 覆盖三种会员等级的限额行为：FREE (5次)、BASIC (100次)、PROFESSIONAL (无限)

#### Property 1 (Auth): 新用户默认 FREE 会员

验证新注册用户默认分配 FREE 会员等级。

| 测试函数 | 验证内容 | 对应需求 |
|----------|----------|----------|
| `test_new_user_with_phone_has_free_tier` | 手机注册用户默认 FREE | 1.5 |
| `test_new_user_with_email_has_free_tier` | 邮箱注册用户默认 FREE | 1.5 |
| `test_new_user_with_both_phone_and_email_has_free_tier` | 同时有手机和邮箱的用户默认 FREE | 1.5 |
| `test_new_user_membership_expiry_is_none` | 新用户会员过期时间为 None | 1.5 |
| `test_new_user_daily_usage_count_is_zero` | 新用户每日使用次数为 0 | 1.5 |
| `test_user_model_default_membership_tier_is_free` | User 模型默认值验证 | 1.5 |

#### Property 2 (Auth): 验证码发送频率限制

验证短信验证码请求频率限制为每 60 秒一次。

| 测试函数 | 验证内容 | 对应需求 |
|----------|----------|----------|
| `test_rate_limit_rejects_within_60_seconds` | 60 秒内重复请求被拒绝 | 1.6 |
| `test_rate_limit_allows_after_60_seconds` | 60 秒后允许再次请求 | 1.6 |
| `test_rate_limit_exactly_at_60_seconds` | 恰好 60 秒时允许请求 | 1.6 |
| `test_rate_limit_is_per_phone_number` | 频率限制按手机号独立计算 | 1.6 |
| `test_is_rate_limited_returns_true_within_60_seconds` | is_rate_limited 方法正确性 | 1.6 |
| `test_cooldown_remaining_is_accurate` | 剩余冷却时间计算准确 | 1.6 |

#### Property 3 (Auth): 手机号唯一性

验证已注册的手机号不能重复注册。

| 测试函数 | 验证内容 | 对应需求 |
|----------|----------|----------|
| `test_duplicate_phone_registration_rejected` | 重复手机号注册被拒绝 | 1.2 |
| `test_phone_uniqueness_check_returns_true_for_registered` | is_phone_registered 返回正确结果 | 1.2 |
| `test_different_phones_can_register` | 不同手机号可以分别注册 | 1.2 |
| `test_phone_uniqueness_error_message` | 错误消息包含手机号信息 | 1.2 |

#### Property 4 (Auth): Token 刷新有效性

验证使用有效的 Refresh Token 可以获取新的 Token 对。

| 测试函数 | 验证内容 | 对应需求 |
|----------|----------|----------|
| `test_refresh_token_returns_valid_token_pair` | 刷新返回有效的 Token 对 | 2.3 |
| `test_refreshed_access_token_is_verifiable` | 新 Access Token 可验证 | 2.3 |
| `test_refreshed_refresh_token_is_verifiable` | 新 Refresh Token 可验证 | 2.3 |
| `test_refreshed_tokens_are_different_from_original` | 新 Token 与原 Token 不同 | 2.3 |
| `test_access_token_cannot_be_used_for_refresh` | Access Token 不能用于刷新 | 2.3 |
| `test_token_refresh_preserves_user_id` | 刷新后 user_id 保持不变 | 2.3 |

#### Property 5 (Auth): 登出使 Token 失效

验证登出后 Refresh Token 被撤销，无法再用于刷新。

| 测试函数 | 验证内容 | 对应需求 |
|----------|----------|----------|
| `test_logout_invalidates_refresh_token` | 登出后 Token 失效 | 3.1 |
| `test_logout_invalidates_email_user_token` | 邮箱用户登出后 Token 失效 | 3.1 |
| `test_logout_returns_true_for_valid_token` | 有效 Token 登出返回 True | 3.1 |
| `test_double_logout_second_returns_false` | 重复登出返回 False | 3.1 |
| `test_new_login_after_logout_works` | 登出后可以重新登录 | 3.1 |

**测试设计亮点：**

- 使用 Hypothesis 生成随机手机号和邮箱进行测试
- 每个测试创建独立的服务实例，确保测试隔离
- 覆盖手机号和邮箱两种注册/登录方式
- 验证 Token 生命周期管理的完整性

### 运行属性测试

```bash
# 运行所有属性测试
poetry run pytest tests/property/ -v

# 运行特定属性测试文件
poetry run pytest tests/property/test_prompt_builder_props.py -v
poetry run pytest tests/property/test_zimage_client_props.py -v
poetry run pytest tests/property/test_content_filter_props.py -v
poetry run pytest tests/property/test_membership_props.py -v
poetry run pytest tests/property/test_rate_limiter_props.py -v
poetry run pytest tests/property/test_auth_props.py -v
poetry run pytest tests/property/test_sms_props.py -v

# 增加测试迭代次数（默认 100 次）
poetry run pytest tests/property/ -v --hypothesis-seed=0
```

---

## 集成测试

集成测试用于验证 API 端点的完整行为，包括认证、限流、错误处理等。

### 测试文件

| 文件 | 测试范围 | 说明 |
|------|----------|------|
| `tests/integration/test_api_integration.py` | HTTP API 端点 | API 集成测试 |
| `tests/integration/test_poster_integration.py` | 海报生成流程 | 海报生成集成测试 |
| `tests/integration/test_auth_integration.py` | 认证 API 端点 | 认证流程集成测试 |

### Auth API 集成测试

文件路径：`tests/integration/test_auth_integration.py`

验证认证 API 端点的完整行为，对应 Requirements 1.1, 1.7, 2.1, 2.6, 3.1。

#### 测试类结构

| 测试类 | 测试范围 | 对应需求 |
|--------|----------|----------|
| `TestSendVerificationCode` | 发送验证码 | 1.4, 1.6 |
| `TestPhoneRegistration` | 手机号注册 | 1.1, 1.2, 1.3, 1.5 |
| `TestEmailRegistration` | 邮箱注册 | 1.5, 1.7 |
| `TestPhoneLogin` | 手机号登录 | 2.1 |
| `TestEmailLogin` | 邮箱登录 | 2.6 |
| `TestTokenRefresh` | Token 刷新 | 2.3, 2.4, 3.1 |
| `TestLogout` | 登出 | 3.1 |
| `TestGetCurrentUser` | 获取当前用户 | 2.5 |
| `TestFullAuthFlow` | 完整认证流程 | 1.7, 2.3, 2.6, 3.1 |

#### 测试用例详情

**TestSendVerificationCode - 发送验证码**

| 测试函数 | 验证内容 | 对应需求 |
|----------|----------|----------|
| `test_send_code_success` | 成功发送验证码 | 1.6 |
| `test_send_code_invalid_phone` | 无效手机号返回 422 | 1.4 |
| `test_send_code_invalid_phone_format` | 格式错误的手机号返回 422 | 1.4 |

**TestPhoneRegistration - 手机号注册**

| 测试函数 | 验证内容 | 对应需求 |
|----------|----------|----------|
| `test_register_phone_success` | 成功注册并返回 FREE 会员 | 1.1, 1.5 |
| `test_register_phone_already_exists` | 重复手机号返回 409 | 1.2 |
| `test_register_phone_invalid_code` | 无效验证码返回 400 | 1.3 |

**TestEmailRegistration - 邮箱注册**

| 测试函数 | 验证内容 | 对应需求 |
|----------|----------|----------|
| `test_register_email_success` | 成功注册并返回 FREE 会员 | 1.5, 1.7 |
| `test_register_email_already_exists` | 重复邮箱返回 409 | 1.7 |
| `test_register_email_weak_password` | 弱密码返回 422 | 1.7 |
| `test_register_email_invalid_format` | 无效邮箱格式返回 422 | 1.7 |

**TestPhoneLogin - 手机号登录**

| 测试函数 | 验证内容 | 对应需求 |
|----------|----------|----------|
| `test_login_phone_success` | 成功登录并返回 Token | 2.1 |
| `test_login_phone_user_not_found` | 未注册用户返回 401 | 2.1 |
| `test_login_phone_invalid_code` | 无效验证码返回 401 | 2.1 |

**TestEmailLogin - 邮箱登录**

| 测试函数 | 验证内容 | 对应需求 |
|----------|----------|----------|
| `test_login_email_success` | 成功登录并返回 Token | 2.6 |
| `test_login_email_wrong_password` | 错误密码返回 401 | 2.6 |
| `test_login_email_not_found` | 未注册邮箱返回 401 | 2.6 |

**TestTokenRefresh - Token 刷新**

| 测试函数 | 验证内容 | 对应需求 |
|----------|----------|----------|
| `test_refresh_token_success` | 成功刷新并返回新 Token | 2.3 |
| `test_refresh_token_invalid` | 无效 Token 返回 401 | 2.4 |
| `test_refresh_token_after_logout` | 登出后刷新返回 401 | 3.1 |

**TestLogout - 登出**

| 测试函数 | 验证内容 | 对应需求 |
|----------|----------|----------|
| `test_logout_success` | 成功登出 | 3.1 |
| `test_logout_invalid_token` | 无效 Token 登出返回 success=false | 3.1 |

**TestGetCurrentUser - 获取当前用户**

| 测试函数 | 验证内容 | 对应需求 |
|----------|----------|----------|
| `test_get_me_success` | 成功获取用户信息 | 2.5 |
| `test_get_me_no_token` | 无 Token 返回 401 | 2.5 |
| `test_get_me_invalid_token` | 无效 Token 返回 401 | 2.5 |

**TestFullAuthFlow - 完整认证流程**

| 测试函数 | 验证内容 | 对应需求 |
|----------|----------|----------|
| `test_email_registration_login_refresh_logout_flow` | 完整的邮箱认证流程 | 1.7, 2.3, 2.6, 3.1 |

### API 集成测试

文件路径：`tests/integration/test_api_integration.py`

验证 HTTP API 端点的行为，对应 Requirements 1.1, 2.1, 3.1, 4.1, 6.1, 7.1。

#### 测试类结构

| 测试类 | 测试范围 | 对应需求 |
|--------|----------|----------|
| `TestHealthEndpoints` | 健康检查和根端点 | - |
| `TestPosterGenerationAPI` | 海报生成 API | 1.1, 2.2, 6.1, 7.1, 7.2 |
| `TestTemplatesAPI` | 模板 API | 3.1, 3.2, 3.3 |
| `TestSceneFusionAPI` | 场景融合 API | 7.4 |
| `TestErrorResponseFormat` | 错误响应格式 | - |

#### 测试用例详情

**TestHealthEndpoints - 健康检查端点**

| 测试函数 | 验证内容 |
|----------|----------|
| `test_health_check` | 健康检查端点返回 healthy 状态 |
| `test_root_endpoint` | 根端点返回 API 信息 |

**TestPosterGenerationAPI - 海报生成 API**

| 测试函数 | 验证内容 | 对应需求 |
|----------|----------|----------|
| `test_generate_poster_requires_auth` | 海报生成需要认证 | 7.1 |
| `test_generate_poster_success` | 成功生成中文海报 | 1.1 |
| `test_generate_poster_rate_limit_exceeded` | 超出限额返回 429 | 7.2 |
| `test_generate_poster_content_blocked` | 敏感内容返回 400 | 6.1 |
| `test_get_quota` | 获取用户配额信息 | 7.2 |
| `test_generate_poster_batch_mode` | 批量生成 4 张预览图 | 2.2 |

**TestTemplatesAPI - 模板 API**

| 测试函数 | 验证内容 | 对应需求 |
|----------|----------|----------|
| `test_list_templates` | 列出所有模板 | 3.1 |
| `test_list_templates_by_category` | 按分类筛选模板 | 3.1, 3.2, 3.3 |
| `test_get_template_by_id` | 根据 ID 获取模板 | 3.1 |
| `test_get_template_not_found` | 不存在的模板返回 404 | - |
| `test_get_holiday_templates` | 获取节日模板 | 3.3 |
| `test_get_categories_summary` | 获取分类统计 | - |

**TestSceneFusionAPI - 场景融合 API**

| 测试函数 | 验证内容 | 对应需求 |
|----------|----------|----------|
| `test_scene_fusion_requires_auth` | 场景融合需要认证 | 7.4 |
| `test_scene_fusion_requires_professional_tier` | 需要专业会员 | 7.4 |
| `test_scene_fusion_basic_member_denied` | 基础会员被拒绝 | 7.4 |
| `test_check_scene_fusion_access_free` | 免费用户权限检查 | 7.4 |
| `test_check_scene_fusion_access_professional` | 专业会员权限检查 | 7.4 |
| `test_scene_fusion_upload_invalid_format` | 无效图片格式返回 400 | - |

**TestErrorResponseFormat - 错误响应格式**

| 测试函数 | 验证内容 |
|----------|----------|
| `test_not_found_error_format` | 404 错误响应格式 |
| `test_unauthorized_error_format` | 401 错误响应格式 |
| `test_forbidden_error_format` | 403 错误响应格式 |

#### 测试设计特点

**依赖注入模式：**

测试使用 FastAPI 的 `dependency_overrides` 机制注入 mock 依赖：

```python
from app.utils.rate_limiter import get_rate_limiter
from app.services.poster_service import get_poster_service

# 注入 mock 依赖
app.dependency_overrides[get_rate_limiter] = lambda: mock_rate_limiter
app.dependency_overrides[get_poster_service] = lambda: mock_poster_service

try:
    response = client.post("/api/poster/generate", ...)
finally:
    app.dependency_overrides.clear()  # 清理依赖覆盖
```

**pytest Fixture：**

测试使用 pytest fixture 管理共享的 mock 对象：

```python
@pytest.fixture
def mock_rate_limiter():
    """Create a mock rate limiter."""
    mock = AsyncMock(spec=RateLimiter)
    mock.check_limit.return_value = RateLimitResult(allowed=True, remaining_quota=4)
    return mock

@pytest.fixture
def mock_poster_service():
    """Create a mock poster service."""
    mock = AsyncMock(spec=PosterService)
    mock.generate_poster.return_value = PosterGenerationResponse(...)
    return mock
```

### 运行集成测试

```bash
# 运行所有集成测试
poetry run pytest tests/integration/ -v

# 运行特定集成测试文件
poetry run pytest tests/integration/test_api_integration.py -v
poetry run pytest tests/integration/test_poster_integration.py -v

# 运行特定测试类
poetry run pytest tests/integration/test_api_integration.py::TestPosterGenerationAPI -v

# 运行特定测试函数
poetry run pytest tests/integration/test_api_integration.py::TestPosterGenerationAPI::test_generate_poster_success -v
```

---

## 单元测试

单元测试用于验证特定示例和边界情况，确保各模块功能正确。

### 测试文件

| 文件 | 测试模块 | 说明 |
|------|----------|------|
| `tests/unit/test_template_service.py` | TemplateService | 模板服务单元测试 |
| `tests/unit/test_content_filter.py` | ContentFilterService | 敏感词过滤单元测试 |
| `tests/unit/test_scene_fusion_service.py` | SceneFusionService | 场景融合服务单元测试 |

### TemplateService 单元测试

文件路径：`tests/unit/test_template_service.py`

验证模板服务的加载、查询和应用功能，对应 Requirements 3.1-3.4。

#### 测试类结构

| 测试类 | 测试范围 | 对应需求 |
|--------|----------|----------|
| `TestTemplateLoading` | 模板加载验证 | 3.1, 3.2, 3.3 |
| `TestPromotionalTemplates` | 促销类模板测试 | 3.1 |
| `TestPremiumTemplates` | 高级类模板测试 | 3.2 |
| `TestHolidayTemplates` | 节日类模板测试 | 3.3 |
| `TestTemplateServiceListTemplates` | list_templates 方法测试 | 3.1, 3.2, 3.3 |
| `TestTemplateServiceGetTemplate` | get_template 方法测试 | 3.1, 3.2, 3.3 |
| `TestTemplateServiceGetTemplatesByHoliday` | get_templates_by_holiday 方法测试 | 3.3 |
| `TestTemplateServiceApplyTemplate` | apply_template 方法测试 | 3.4 |

#### 测试用例详情

**TestTemplateLoading - 模板加载验证**

| 测试函数 | 验证内容 |
|----------|----------|
| `test_all_templates_loaded` | 验证 9 个模板全部加载（3 促销 + 3 高级 + 3 节日） |
| `test_template_by_id_lookup` | 验证通过 ID 查找模板功能 |
| `test_promotional_templates_have_correct_category` | 验证促销模板分类正确 |
| `test_premium_templates_have_correct_category` | 验证高级模板分类正确 |
| `test_holiday_templates_have_correct_category` | 验证节日模板分类正确且有节日类型 |
| `test_all_templates_have_required_fields` | 验证所有模板必需字段完整 |
| `test_all_templates_have_valid_prompt_modifiers` | 验证所有模板的 prompt_modifiers 有效 |

**TestPromotionalTemplates - 促销类模板测试 (Requirements 3.1)**

| 测试函数 | 验证内容 |
|----------|----------|
| `test_promotional_template_has_red_background` | 验证促销模板包含红色背景 |
| `test_promotional_template_has_explosion_style` | 验证促销模板包含爆炸贴纸风格 |
| `test_promotional_template_has_large_font` | 验证促销模板包含大字号 |

**TestPremiumTemplates - 高级类模板测试 (Requirements 3.2)**

| 测试函数 | 验证内容 |
|----------|----------|
| `test_premium_minimal_has_whitespace` | 验证极简模板包含留白 |
| `test_premium_studio_has_lighting` | 验证影棚模板包含光效 |
| `test_premium_blackgold_has_correct_colors` | 验证黑金模板包含黑金配色 |

**TestHolidayTemplates - 节日类模板测试 (Requirements 3.3)**

| 测试函数 | 验证内容 |
|----------|----------|
| `test_spring_festival_template` | 验证春节模板包含正确的节日元素 |
| `test_valentines_template` | 验证情人节模板包含正确的节日元素 |
| `test_double_eleven_template` | 验证双十一模板包含正确的节日元素 |

**TestTemplateServiceApplyTemplate - 模板应用测试 (Requirements 3.4)**

| 测试函数 | 验证内容 |
|----------|----------|
| `test_apply_template_combines_template_and_user_input` | 验证模板参数和用户输入正确合并 |
| `test_apply_template_includes_style_keywords` | 验证应用模板时包含风格关键词 |
| `test_apply_template_includes_color_scheme` | 验证应用模板时包含配色方案 |
| `test_apply_template_includes_layout_hints` | 验证应用模板时包含排版提示 |
| `test_apply_template_includes_font_style` | 验证应用模板时包含字体风格 |
| `test_apply_template_with_english_text` | 验证应用模板时支持英文文案 |
| `test_apply_nonexistent_template_raises_error` | 验证应用不存在的模板抛出错误 |
| `test_apply_holiday_template_includes_festival_elements` | 验证应用节日模板时包含节日元素 |

### ContentFilterService 单元测试

文件路径：`tests/unit/test_content_filter.py`

验证敏感词过滤服务的功能，对应 Requirements 6.1。

| 测试类 | 测试范围 |
|--------|----------|
| `TestContentFilterWithKnownSensitiveWords` | 已知敏感词被正确过滤 |
| `TestContentFilterWithNormalContent` | 正常内容通过过滤 |
| `TestContentFilterBlocklistManagement` | 敏感词列表管理功能 |
| `TestContentFilterSingleton` | 单例模式测试 |

### 运行单元测试

```bash
# 运行所有单元测试
poetry run pytest tests/unit/ -v

# 运行特定单元测试文件
poetry run pytest tests/unit/test_template_service.py -v
poetry run pytest tests/unit/test_content_filter.py -v

# 运行特定测试类
poetry run pytest tests/unit/test_template_service.py::TestTemplateServiceApplyTemplate -v

# 运行特定测试函数
poetry run pytest tests/unit/test_template_service.py::TestTemplateServiceApplyTemplate::test_apply_template_combines_template_and_user_input -v
```

### 测试策略说明

属性测试使用 Hypothesis 策略生成随机测试数据：

| 策略 | 说明 |
|------|------|
| `chinese_chars` | 生成 CJK 统一汉字 (U+4E00-U+9FFF) |
| `english_chars` | 生成 ASCII 字母、数字和常用标点 |
| `mixed_text` | 随机选择中文或英文文本 |
| `scene_description` | 生成中英文混合的场景描述 |
| `aspect_ratio` | 从 1:1, 9:16, 16:9 中随机选择 |
| `batch_size` | 从 1, 4 中随机选择 |
| `style_keywords_list` | 生成 1-5 个风格关键词列表 |
| `color_scheme` | 生成配色方案字符串 |
| `layout_hints` | 生成排版提示字符串 |
| `font_style` | 生成字体风格字符串 |
| `sensitive_keyword` | 生成敏感词（中英文混合，2-20 字符） |
| `blocklist_strategy` | 生成敏感词列表（1-10 个唯一关键词） |
| `safe_text_chars` | 生成安全文本（纯数字和符号，避免意外匹配） |
| `surrounding_text` | 生成敏感词周围的文本 |
| `usage_count_strategy` | 生成使用次数（0-100） |
| `user_id_strategy` | 生成用户 ID（5-20 字符的字母数字组合） |
| `membership_tier_strategy` | 从 FREE/BASIC/PROFESSIONAL 中随机选择会员等级 |
| `watermark_text_strategy` | 生成水印文本（1-50 字符的字母数字组合） |
| `base_size` | 生成图像基础尺寸（256-2048） |
| `batch_count` | 生成批量数量（1-10） |
| `prompt_text` | 生成 Prompt 文本（1-200 字符，非空白） |
