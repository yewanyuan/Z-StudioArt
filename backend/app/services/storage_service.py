"""Storage Service for PopGraph.

保存生成的图片到数据库。
"""

import base64
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import GeneratedImageRecord, GenerationRecord, get_async_session_maker
from app.models.schemas import GenerationType, PosterGenerationRequest, PosterGenerationResponse


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
        """
        session_maker = get_async_session_maker()
        async with session_maker() as session:
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
                    image_data = base64.b64decode(img.image_base64)
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
    
    async def get_image(self, image_id: str) -> Optional[bytes]:
        """从数据库获取图片
        
        Args:
            image_id: 图片 ID
            
        Returns:
            图片二进制数据，如果不存在返回 None
        """
        session_maker = get_async_session_maker()
        async with session_maker() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(GeneratedImageRecord).where(GeneratedImageRecord.id == image_id)
            )
            record = result.scalar_one_or_none()
            if record:
                return record.image_data
            return None


_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """获取存储服务实例"""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
