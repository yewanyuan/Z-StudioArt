"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import poster, templates, scene_fusion, upload

app = FastAPI(
    title="PopGraph API",
    description="爆款图 - AI 图文一体化生成平台",
    version="0.1.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(poster.router)
app.include_router(templates.router)
app.include_router(scene_fusion.router)
app.include_router(upload.router)


@app.get("/health")
async def health_check():
    """健康检查端点。"""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """根路径端点。"""
    return {
        "name": "PopGraph API",
        "version": "0.1.0",
        "description": "爆款图 - AI 图文一体化生成平台",
        "docs_url": "/docs",
    }
