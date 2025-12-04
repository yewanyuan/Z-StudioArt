"""Upload API for PopGraph.

处理文件上传。
"""

import base64
import uuid
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post(
    "/product",
    summary="上传商品图片",
    description="上传商品白底图，返回 base64 数据 URL",
)
async def upload_product_image(
    file: Annotated[UploadFile, File(description="商品白底图")],
) -> dict:
    """上传商品图片
    
    Args:
        file: 上传的图片文件
        
    Returns:
        包含图片 URL 的字典
    """
    # 验证文件类型
    if file.content_type not in ["image/png", "image/jpeg", "image/jpg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_IMAGE", "message": "不支持的图片格式，请上传 PNG 或 JPEG 格式"},
        )
    
    # 读取文件内容
    content = await file.read()
    
    # 转换为 base64 data URL
    content_type = file.content_type or "image/png"
    base64_data = base64.b64encode(content).decode("utf-8")
    data_url = f"data:{content_type};base64,{base64_data}"
    
    return {"url": data_url}
