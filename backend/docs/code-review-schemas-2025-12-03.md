# 代码审查报告: schemas.py

**文件**: `backend/app/models/schemas.py`  
**审查日期**: 2025-12-03  
**审查结论**: 整体质量良好，有几处可优化

---

## 问题 1: ExtractedProduct 使用 bytes 类型

### 位置
```python
class ExtractedProduct(BaseModel):
    image_data: bytes = Field(..., description="商品图像数据")
    mask: bytes = Field(..., description="商品遮罩")
```

### 为什么是问题
- `bytes` 类型在 JSON 序列化时会出问题
- 不适合通过 API 传输
- Pydantic v2 对 bytes 的处理需要额外配置

### 改进建议
```python
from pydantic import Base64Bytes

class ExtractedProduct(BaseModel):
    """提取的商品信息 Schema (内部使用)"""
    image_data: Base64Bytes = Field(..., description="商品图像数据(Base64)")
    mask: Base64Bytes = Field(..., description="商品遮罩(Base64)")
    bounding_box: tuple[int, int, int, int] = Field(..., description="边界框(x, y, w, h)")
    
    model_config = {"arbitrary_types_allowed": True}
```

或者如果仅内部使用，添加注释说明：

```python
class ExtractedProduct(BaseModel):
    """提取的商品信息 Schema
    
    注意: 此 Schema 仅用于服务内部传递，不通过 API 暴露
    """
```

### 预期收益
- 避免序列化错误
- 明确使用场景

---

## 问题 2: aspect_ratio 重复定义

### 位置
```python
# PosterGenerationRequest 中
aspect_ratio: Literal["1:1", "9:16", "16:9"]

# SceneFusionRequest 中  
aspect_ratio: Literal["1:1", "9:16", "16:9"]
```

### 为什么是问题
- 违反 DRY (Don't Repeat Yourself) 原则
- 如果需要添加新尺寸，要改多处
- 容易遗漏导致不一致

### 改进建议
```python
# 在 Enums 区域添加类型别名
AspectRatio = Literal["1:1", "9:16", "16:9"]

# 或使用 Enum 更规范
class AspectRatio(str, Enum):
    """输出尺寸比例枚举"""
    SQUARE = "1:1"        # 微信朋友圈
    MOBILE = "9:16"       # 手机海报
    VIDEO_COVER = "16:9"  # 视频封面

# 使用
class PosterGenerationRequest(BaseModel):
    aspect_ratio: AspectRatio = Field(..., description="输出尺寸比例")
```

### 预期收益
- 单点维护
- 类型安全
- 更好的代码提示

---

## 问题 3: 缺少字段验证

### 位置
```python
class PosterGenerationRequest(BaseModel):
    scene_description: str = Field(..., description="画面描述")
    marketing_text: str = Field(..., description="指定文案")
```

### 为什么是问题
- 没有长度限制，可能接受超长输入
- 没有非空验证
- 可能导致 AI 模型调用失败或资源浪费

### 改进建议
```python
from pydantic import Field, field_validator

class PosterGenerationRequest(BaseModel):
    scene_description: str = Field(
        ..., 
        min_length=1,
        max_length=500,
        description="画面描述"
    )
    marketing_text: str = Field(
        ..., 
        min_length=1,
        max_length=100,
        description="指定文案"
    )
    
    @field_validator("scene_description", "marketing_text")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()
```

### 预期收益
- 防止无效输入
- 提前失败，节省资源
- 更好的错误提示

---

## 问题 4: RATE_LIMIT_CONFIG 类型不够精确

### 位置
```python
RATE_LIMIT_CONFIG: dict[MembershipTier, dict] = {
    MembershipTier.FREE: {"daily_limit": 5, "priority": "low"},
    ...
}
```

### 为什么是问题
- `dict` 类型太宽泛，没有类型检查
- IDE 无法提供正确的代码补全
- 容易写错 key 名

### 改进建议
```python
from typing import TypedDict

class RateLimitSettings(TypedDict):
    """限流配置类型"""
    daily_limit: int  # -1 表示无限
    priority: Literal["low", "normal", "high"]

RATE_LIMIT_CONFIG: dict[MembershipTier, RateLimitSettings] = {
    MembershipTier.FREE: {"daily_limit": 5, "priority": "low"},
    MembershipTier.BASIC: {"daily_limit": 100, "priority": "normal"},
    MembershipTier.PROFESSIONAL: {"daily_limit": -1, "priority": "high"},
}
```

### 预期收益
- 完整的类型检查
- IDE 智能提示
- 减少运行时错误

---

## 总结

| 优先级 | 问题 | 建议 |
|--------|------|------|
| 🔴 高 | 字段验证缺失 | 添加长度限制和验证器 |
| 🟡 中 | aspect_ratio 重复 | 提取为类型别名或 Enum |
| 🟡 中 | RATE_LIMIT_CONFIG 类型 | 使用 TypedDict |
| 🟢 低 | ExtractedProduct bytes | 添加注释或改用 Base64 |

建议按优先级逐步改进，确保每次修改后测试通过。
