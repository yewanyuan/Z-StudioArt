"""History API for PopGraph.

This module implements the history API endpoints for managing user generation history.

Requirements:
- 6.1: WHEN a user requests generation history THEN THE User_System SHALL return 
       a paginated list of generation records sorted by creation time descending
- 6.3: WHEN a user clicks on a history record THEN THE User_System SHALL display 
       the full-size image and allow download
- 6.4: WHEN a user deletes a history record THEN THE User_System SHALL remove 
       the record and associated images from storage
"""

from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.models.database import User, get_db_session
from app.models.schemas import GenerationType
from app.services.history_service import HistoryService


router = APIRouter(prefix="/api/history", tags=["history"])


# ============================================================================
# Request/Response Schemas
# ============================================================================

class HistoryItem(BaseModel):
    """历史记录项 Schema"""
    id: str = Field(..., description="记录唯一标识")
    type: GenerationType = Field(..., description="生成类型")
    thumbnail_url: Optional[str] = Field(None, description="缩略图URL")
    created_at: datetime = Field(..., description="创建时间")
    input_params: dict = Field(..., description="输入参数")
    output_urls: list[str] = Field(..., description="输出图片URL列表")
    processing_time_ms: int = Field(..., description="处理时间(毫秒)")
    has_watermark: bool = Field(..., description="是否有水印")


class HistoryListResponse(BaseModel):
    """历史记录列表响应 Schema"""
    items: list[HistoryItem] = Field(..., description="历史记录列表")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    has_more: bool = Field(..., description="是否有更多记录")


class HistoryDetailResponse(BaseModel):
    """历史记录详情响应 Schema"""
    id: str = Field(..., description="记录唯一标识")
    type: GenerationType = Field(..., description="生成类型")
    created_at: datetime = Field(..., description="创建时间")
    input_params: dict = Field(..., description="输入参数")
    output_urls: list[str] = Field(..., description="输出图片URL列表")
    processing_time_ms: int = Field(..., description="处理时间(毫秒)")
    has_watermark: bool = Field(..., description="是否有水印")


class DeleteResponse(BaseModel):
    """删除响应 Schema"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")


# ============================================================================
# Error Codes
# ============================================================================

class HistoryErrorCode:
    """历史记录错误码定义"""
    RECORD_NOT_FOUND = "RECORD_NOT_FOUND"
    DELETE_FAILED = "DELETE_FAILED"


# ============================================================================
# Dependencies
# ============================================================================

async def get_history_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> HistoryService:
    """获取历史记录服务实例"""
    return HistoryService(db)


# ============================================================================
# API Endpoints
# ============================================================================

@router.get(
    "",
    response_model=HistoryListResponse,
    summary="获取历史记录列表",
    description="获取当前用户的生成历史记录列表，支持分页",
    responses={
        401: {"description": "未认证"},
    },
)
async def get_history_list(
    current_user: Annotated[User, Depends(get_current_user)],
    history_service: Annotated[HistoryService, Depends(get_history_service)],
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> HistoryListResponse:
    """获取历史记录列表
    
    Requirements:
    - 6.1: WHEN a user requests generation history THEN THE User_System SHALL return 
           a paginated list of generation records sorted by creation time descending
    
    Args:
        current_user: 当前认证的用户
        history_service: 历史记录服务
        page: 页码（从1开始）
        page_size: 每页数量（1-100）
        
    Returns:
        分页的历史记录列表
    """
    records, total = await history_service.get_user_history(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    
    items = [
        HistoryItem(
            id=record.id,
            type=record.type,
            thumbnail_url=record.output_urls[0] if record.output_urls else None,
            created_at=record.created_at,
            input_params=record.input_params,
            output_urls=record.output_urls,
            processing_time_ms=record.processing_time_ms,
            has_watermark=record.has_watermark,
        )
        for record in records
    ]
    
    has_more = (page * page_size) < total
    
    return HistoryListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more,
    )


@router.get(
    "/{record_id}",
    response_model=HistoryDetailResponse,
    summary="获取记录详情",
    description="获取指定历史记录的详细信息",
    responses={
        401: {"description": "未认证"},
        404: {"description": "记录不存在"},
    },
)
async def get_history_detail(
    record_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    history_service: Annotated[HistoryService, Depends(get_history_service)],
) -> HistoryDetailResponse:
    """获取记录详情
    
    Requirements:
    - 6.3: WHEN a user clicks on a history record THEN THE User_System SHALL display 
           the full-size image and allow download
    
    Args:
        record_id: 记录ID
        current_user: 当前认证的用户
        history_service: 历史记录服务
        
    Returns:
        历史记录详情
        
    Raises:
        HTTPException: 如果记录不存在或不属于当前用户
    """
    record = await history_service.get_record_detail(
        record_id=record_id,
        user_id=current_user.id,
    )
    
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": HistoryErrorCode.RECORD_NOT_FOUND,
                "message": "记录不存在或无权访问",
            },
        )
    
    return HistoryDetailResponse(
        id=record.id,
        type=record.type,
        created_at=record.created_at,
        input_params=record.input_params,
        output_urls=record.output_urls,
        processing_time_ms=record.processing_time_ms,
        has_watermark=record.has_watermark,
    )


@router.delete(
    "/{record_id}",
    response_model=DeleteResponse,
    summary="删除记录",
    description="删除指定的历史记录及其关联的图片",
    responses={
        401: {"description": "未认证"},
        404: {"description": "记录不存在"},
    },
)
async def delete_history_record(
    record_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    history_service: Annotated[HistoryService, Depends(get_history_service)],
) -> DeleteResponse:
    """删除历史记录
    
    Requirements:
    - 6.4: WHEN a user deletes a history record THEN THE User_System SHALL remove 
           the record and associated images from storage
    
    Args:
        record_id: 记录ID
        current_user: 当前认证的用户
        history_service: 历史记录服务
        
    Returns:
        删除结果
        
    Raises:
        HTTPException: 如果记录不存在或不属于当前用户
    """
    success = await history_service.delete_record(
        record_id=record_id,
        user_id=current_user.id,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": HistoryErrorCode.RECORD_NOT_FOUND,
                "message": "记录不存在或无权删除",
            },
        )
    
    return DeleteResponse(
        success=True,
        message="记录已删除",
    )
