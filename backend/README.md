# PopGraph Backend

爆款图 - AI 图文一体化生成平台后端服务

## 技术栈

- Python 3.11+
- FastAPI
- SQLAlchemy (PostgreSQL)
- Redis
- Pillow
- Hypothesis (属性测试)

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
│   │   ├── database.py   # SQLAlchemy 模型 (User, GenerationRecord, TemplateRecord)
│   │   └── schemas.py    # Pydantic Schema 定义
│   ├── services/     # 业务服务
│   ├── utils/        # 工具模块
│   │   └── prompt_builder.py  # Prompt 构建器
│   └── main.py       # 应用入口
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

### SQLAlchemy 模型 (`app/models/database.py`)

- `User`: 用户模型，包含会员等级和使用配额
- `GenerationRecord`: 生成记录
- `GeneratedImageRecord`: 生成图片记录，存储图片二进制数据
- `TemplateRecord`: 模板存储

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

## API 路由模块

### PosterAPI (`app/api/poster.py`)

海报生成 API 模块，提供海报生成和配额查询端点。

| 端点 | 方法 | 功能 | 相关需求 |
|------|------|------|----------|
| `/api/poster/generate` | POST | 生成商业海报 | 1.1, 1.2, 2.1, 2.2, 6.1, 7.1, 7.2, 7.3 |
| `/api/poster/quota` | GET | 获取用户剩余配额 | 7.2 |

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

**特性：**
- 完整的认证和限流检查
- 敏感内容过滤（在服务层处理）
- 生成成功后才增加使用计数
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

## 核心服务模块

### MembershipService (`app/services/membership_service.py`)

会员权限服务，负责处理会员相关的业务逻辑，包括水印规则判断和功能权限检查。

| 方法 | 功能 | 相关需求 |
|------|------|----------|
| `should_add_watermark()` | 判断是否需要添加水印 | 7.1, 7.3 |
| `get_watermark_rule()` | 获取水印规则详情 | 7.1, 7.3 |
| `has_feature_access()` | 检查会员是否有权访问指定功能 | 7.4 |
| `check_feature_access()` | 检查功能访问权限并返回详细结果 | 7.4 |
| `can_access_scene_fusion()` | 检查是否可以访问场景融合功能 | 7.4 |
| `has_priority_processing()` | 检查是否享有优先处理 | 7.3 |
| `get_tier_features()` | 获取指定会员等级可用的所有功能 | 7.1, 7.3, 7.4 |

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

图片存储服务，负责将生成的图片和记录保存到数据库。

| 方法 | 功能 | 相关需求 |
|------|------|----------|
| `save_generation()` | 保存生成记录和图片到数据库 | 8.1 |
| `get_image()` | 从数据库获取图片二进制数据 | 8.1 |

**使用示例：**

```python
from app.services.storage_service import StorageService, get_storage_service
from app.models.schemas import PosterGenerationRequest, PosterGenerationResponse

# 使用全局单例
storage = get_storage_service()

# 保存生成记录和图片
request = PosterGenerationRequest(
    scene_description="夏日海滩促销",
    marketing_text="限时特惠",
    language="zh",
    aspect_ratio="1:1",
)
response = PosterGenerationResponse(
    request_id="uuid-xxx",
    images=[...],
    processing_time_ms=1500,
)
record_id = await storage.save_generation(
    user_id="user123",
    request=request,
    response=response,
)

# 获取图片数据
image_data = await storage.get_image("image-uuid")
if image_data:
    with open("output.png", "wb") as f:
        f.write(image_data)
```

**特性：**
- 自动解码 Base64 图片数据并存储为二进制
- 保存完整的生成参数（场景描述、营销文案、宽高比等）
- 关联 `GenerationRecord` 和 `GeneratedImageRecord`
- 全局单例访问模式
- 异步数据库操作

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
