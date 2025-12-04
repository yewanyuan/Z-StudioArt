"""Template API for PopGraph.

This module implements the template management API endpoints.

Requirements:
- 3.1: 促销类模板（红色背景、爆炸贴纸风格、大字号）
- 3.2: 高级类模板（极简留白、影棚光效、黑金配色）
- 3.3: 节日类模板（春节、情人节、双十一）
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.schemas import Template, TemplateCategory, HolidayType
from app.services.template_service import TemplateService


router = APIRouter(prefix="/api/templates", tags=["templates"])


# ============================================================================
# Dependencies
# ============================================================================

def get_template_service() -> TemplateService:
    """获取模板服务实例"""
    return TemplateService()


# ============================================================================
# API Endpoints
# ============================================================================

@router.get(
    "",
    response_model=list[Template],
    summary="获取模板列表",
    description="获取所有可用的海报模板，可按分类筛选",
    responses={
        200: {"description": "成功返回模板列表"},
    },
)
async def list_templates(
    category: Annotated[
        Optional[TemplateCategory],
        Query(description="模板分类筛选：promotional(促销)、premium(高级)、holiday(节日)")
    ] = None,
    template_service: Annotated[TemplateService, Depends(get_template_service)] = None,
) -> list[Template]:
    """获取模板列表
    
    返回所有可用的海报模板，支持按分类筛选。
    
    Args:
        category: 可选的模板分类筛选
        template_service: 模板服务
        
    Returns:
        模板列表
        
    Requirements:
    - 3.1: 促销类模板
    - 3.2: 高级类模板
    - 3.3: 节日类模板
    """
    return await template_service.list_templates(category)


@router.get(
    "/{template_id}",
    response_model=Template,
    summary="获取模板详情",
    description="根据模板 ID 获取模板详细信息",
    responses={
        200: {"description": "成功返回模板详情"},
        404: {"description": "模板未找到"},
    },
)
async def get_template(
    template_id: str,
    template_service: Annotated[TemplateService, Depends(get_template_service)] = None,
) -> Template:
    """获取模板详情
    
    Args:
        template_id: 模板 ID
        template_service: 模板服务
        
    Returns:
        模板详情
        
    Raises:
        HTTPException: 如果模板未找到
    """
    template = await template_service.get_template(template_id)
    
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "TEMPLATE_NOT_FOUND",
                "message": f"模板未找到: {template_id}",
            },
        )
    
    return template


@router.get(
    "/holiday/{holiday_type}",
    response_model=list[Template],
    summary="获取节日模板",
    description="根据节日类型获取对应的模板",
    responses={
        200: {"description": "成功返回节日模板列表"},
    },
)
async def get_holiday_templates(
    holiday_type: HolidayType,
    template_service: Annotated[TemplateService, Depends(get_template_service)] = None,
) -> list[Template]:
    """获取节日模板
    
    根据节日类型返回对应的模板列表。
    
    Args:
        holiday_type: 节日类型（spring_festival/valentines/double_eleven）
        template_service: 模板服务
        
    Returns:
        节日模板列表
        
    Requirements: 3.3 - 节日类模板
    """
    return await template_service.get_templates_by_holiday(holiday_type)


@router.get(
    "/categories/summary",
    summary="获取模板分类摘要",
    description="获取各分类的模板数量统计",
)
async def get_categories_summary(
    template_service: Annotated[TemplateService, Depends(get_template_service)] = None,
) -> dict:
    """获取模板分类摘要
    
    返回各分类的模板数量统计信息。
    
    Args:
        template_service: 模板服务
        
    Returns:
        分类摘要信息
    """
    all_templates = await template_service.list_templates()
    
    summary = {
        "total": len(all_templates),
        "by_category": {},
    }
    
    for category in TemplateCategory:
        category_templates = await template_service.list_templates(category)
        summary["by_category"][category.value] = len(category_templates)
    
    return summary
