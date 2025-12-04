# 代码审查报告：StorageService

**文件**: `backend/app/services/storage_service.py`  
**审查日期**: 2025-12-04  
**审查范围**: 新增的图片存储服务

---

## 🟡 中等问题

### 1. 缺少错误处理和事务回滚

**位置**: 第 36-70 行 `save_generation` 方法

**问题**: 当前实现没有处理以下异常情况：
- `base64.b64decode()` 解码失败
- 数据库写入失败
- 部分图片保存成功后发生错误

**当前代码**:
```python
async with session_maker() as session:
    # ... 创建记录
    await session.commit()
    return response.request_id
```

**建议修复**:
```python
async def save_generation(
    self,
    user_id: str,
    request: PosterGenerationRequest,
    response: PosterGenerationResponse,
    generation_type: GenerationType = GenerationType.POSTER,
) -> str:
    """保存生成记录和图片到数据库"""
    session_maker = get_async_session_maker()
    async with session_maker() as session:
        try:
            # 创建生成记录
            generation_record = GenerationRecord(
                id=response.request_id,
                user_id=user_id,
                type=generation_type,
                input_params={
                    "scene_description": request.scene_description,
                    "marketing_text": request.marketing_text,
                    "language": request.language,
                    "aspect_ratio": request.aspect_ratio,
                    "template_id": request.template_id,
                    "batch_size": request.batch_size,
                },
                output_urls=[img.url for img in response.images],
                processing_time_ms=response.processing_time_ms,
                has_watermark=response.images[0].has_watermark if response.images else False,
            )
            session.add(generation_record)
            
            # 保存每张图片
            for img in response.images:
                if img.image_base64:
                    try:
                        image_data = base64.b64decode(img.image_base64)
                    except Exception as e:
                        raise ValueError(f"无法解码图片 {img.id} 的 Base64 数据: {e}")
                    
                    image_record = GeneratedImageRecord(
                        id=img.id,
                        generation_id=response.request_id,
                        image_data=image_data,
                        width=img.width,
                        height=img.height,
                        has_watermark=img.has_watermark,
                    )
                    session.add(image_record)
            
            await session.commit()
            return response.request_id
            
        except Exception as e:
            await session.rollback()
            raise
```

**预期收益**: 
- 更健壮的错误处理
- 数据一致性保证
- 更清晰的错误信息

---

### 2. 未使用的导入

**位置**: 第 6-10 行

**问题**: `uuid` 和 `AsyncSession` 被导入但未使用。

**当前代码**:
```python
import base64
import uuid  # 未使用
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession  # 未使用
```

**建议修复**:
```python
import base64
from typing import Optional
```

**预期收益**: 代码更简洁，减少不必要的导入。

---

### 3. `get_image` 方法中的导入位置不佳

**位置**: 第 83-84 行

**问题**: 在函数内部导入 `select`，这是一种反模式，会影响代码可读性和性能（虽然 Python 会缓存导入）。

**当前代码**:
```python
async def get_image(self, image_id: str) -> Optional[bytes]:
    session_maker = get_async_session_maker()
    async with session_maker() as session:
        from sqlalchemy import select  # 函数内导入
        result = await session.execute(...)
```

**建议修复**:
将导入移到文件顶部：
```python
from sqlalchemy import select

# ... 其他代码 ...

async def get_image(self, image_id: str) -> Optional[bytes]:
    session_maker = get_async_session_maker()
    async with session_maker() as session:
        result = await session.execute(
            select(GeneratedImageRecord).where(GeneratedImageRecord.id == image_id)
        )
        # ...
```

**预期收益**: 
- 更好的代码组织
- 符合 Python 导入规范
- 更容易发现依赖关系

---

## 🟢 设计建议

### 4. 考虑添加日志记录

**位置**: 整个类

**建议**: 添加日志记录以便于调试和监控。

```python
import logging

logger = logging.getLogger(__name__)

class StorageService:
    """图片存储服务"""
    
    async def save_generation(self, ...) -> str:
        logger.info(f"保存生成记录: request_id={response.request_id}, user_id={user_id}")
        # ... 现有代码 ...
        logger.info(f"成功保存 {len(response.images)} 张图片")
        return response.request_id
    
    async def get_image(self, image_id: str) -> Optional[bytes]:
        logger.debug(f"获取图片: image_id={image_id}")
        # ... 现有代码 ...
        if record:
            logger.debug(f"找到图片: image_id={image_id}, size={len(record.image_data)} bytes")
        else:
            logger.warning(f"图片不存在: image_id={image_id}")
        return record.image_data if record else None
```

**预期收益**: 更好的可观测性和问题排查能力。

---

### 5. 考虑依赖注入模式

**位置**: 第 36 行

**问题**: 直接调用 `get_async_session_maker()` 使得单元测试更困难。

**建议**: 支持依赖注入：

```python
class StorageService:
    """图片存储服务"""
    
    def __init__(self, session_maker=None):
        """初始化存储服务
        
        Args:
            session_maker: 可选的会话工厂，用于测试时注入 mock
        """
        self._session_maker = session_maker
    
    def _get_session_maker(self):
        """获取会话工厂"""
        if self._session_maker is not None:
            return self._session_maker
        return get_async_session_maker()
    
    async def save_generation(self, ...) -> str:
        session_maker = self._get_session_maker()
        # ... 其余代码不变 ...
```

**预期收益**: 
- 更容易编写单元测试
- 符合依赖倒置原则
- 与项目中其他服务的设计模式保持一致

---

## 🟢 做得好的地方

1. **清晰的文档字符串**: 类和方法都有中文注释说明用途和参数
2. **单例模式**: 使用 `get_storage_service()` 提供全局单例访问，与项目其他服务保持一致
3. **类型注解**: 完整的类型注解提高了代码可读性
4. **合理的职责划分**: 服务专注于存储逻辑，职责单一
5. **正确使用异步**: 正确使用 `async/await` 进行数据库操作
6. **Base64 解码**: 正确处理 `image_base64` 可选字段

---

## 📋 修复优先级

| 优先级 | 问题 | 影响 |
|--------|------|------|
| P1 | 缺少错误处理和事务回滚 | 数据一致性风险 |
| P2 | 函数内导入 | 代码规范 |
| P3 | 未使用的导入 | 代码整洁 |
| P3 | 添加日志记录 | 可观测性 |
| P3 | 依赖注入支持 | 可测试性 |

---

## 快速修复建议

以下是最小改动的修复方案：

```python
"""Storage Service for PopGraph.

保存生成的图片到数据库。
"""

import base64
import logging
from typing import Optional

from sqlalchemy import select

from app.models.database import GeneratedImageRecord, GenerationRecord, get_async_session_maker
from app.models.schemas import GenerationType, PosterGenerationRequest, PosterGenerationResponse

logger = logging.getLogger(__name__)


class StorageService:
    """图片存储服务"""
    
    async def save_generation(
        self,
        user_id: str,
        request: PosterGenerationRequest,
        response: PosterGenerationResponse,
        generation_type: GenerationType = GenerationType.POSTER,
    ) -> str:
        """保存生成记录和图片到数据库
        
        Args:
            user_id: 用户 ID
            request: 生成请求
            response: 生成响应
            generation_type: 生成类型
            
        Returns:
            生成记录 ID
            
        Raises:
            ValueError: Base64 解码失败
            Exception: 数据库操作失败
        """
        session_maker = get_async_session_maker()
        async with session_maker() as session:
            try:
                generation_record = GenerationRecord(
                    id=response.request_id,
                    user_id=user_id,
                    type=generation_type,
                    input_params={
                        "scene_description": request.scene_description,
                        "marketing_text": request.marketing_text,
                        "language": request.language,
                        "aspect_ratio": request.aspect_ratio,
                        "template_id": request.template_id,
                        "batch_size": request.batch_size,
                    },
                    output_urls=[img.url for img in response.images],
                    processing_time_ms=response.processing_time_ms,
                    has_watermark=response.images[0].has_watermark if response.images else False,
                )
                session.add(generation_record)
                
                for img in response.images:
                    if img.image_base64:
                        try:
                            image_data = base64.b64decode(img.image_base64)
                        except Exception as e:
                            raise ValueError(f"无法解码图片 {img.id} 的 Base64 数据: {e}")
                        
                        image_record = GeneratedImageRecord(
                            id=img.id,
                            generation_id=response.request_id,
                            image_data=image_data,
                            width=img.width,
                            height=img.height,
                            has_watermark=img.has_watermark,
                        )
                        session.add(image_record)
                
                await session.commit()
                logger.info(f"保存生成记录成功: request_id={response.request_id}")
                return response.request_id
                
            except Exception:
                await session.rollback()
                raise
    
    async def get_image(self, image_id: str) -> Optional[bytes]:
        """从数据库获取图片
        
        Args:
            image_id: 图片 ID
            
        Returns:
            图片二进制数据，如果不存在返回 None
        """
        session_maker = get_async_session_maker()
        async with session_maker() as session:
            result = await session.execute(
                select(GeneratedImageRecord).where(GeneratedImageRecord.id == image_id)
            )
            record = result.scalar_one_or_none()
            return record.image_data if record else None


_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """获取存储服务实例"""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
```
