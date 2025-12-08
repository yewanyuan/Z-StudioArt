"""FastAPI application entry point."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, history, payment, poster, templates, scene_fusion, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    if os.getenv("ENABLE_SCHEDULER", "false").lower() == "true":
        from app.tasks import start_scheduler
        await start_scheduler()
    
    yield
    
    # Shutdown
    if os.getenv("ENABLE_SCHEDULER", "false").lower() == "true":
        from app.tasks import stop_scheduler
        await stop_scheduler()


app = FastAPI(
    title="PopGraph API",
    description="爆款图 - AI 图文一体化生成平台",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 配置
# 生产环境应设置 CORS_ORIGINS 环境变量限制具体域名
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(auth.router)
app.include_router(history.router)
app.include_router(payment.router)
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
