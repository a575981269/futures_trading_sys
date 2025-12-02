"""
FastAPI应用
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any, List
from datetime import datetime

from api.routes import strategy_routes, trading_routes, monitor_routes, data_routes
from utils.logger import get_logger

logger = get_logger(__name__)


def create_app() -> FastAPI:
    """
    创建FastAPI应用
    
    Returns:
        FastAPI应用实例
    """
    app = FastAPI(
        title="量化交易系统API",
        description="期货量化交易系统RESTful API",
        version="1.0.0"
    )
    
    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    app.include_router(strategy_routes.router, prefix="/api/strategy", tags=["策略"])
    app.include_router(trading_routes.router, prefix="/api/trading", tags=["交易"])
    app.include_router(monitor_routes.router, prefix="/api/monitor", tags=["监控"])
    app.include_router(data_routes.router, prefix="/api/data", tags=["数据"])
    
    @app.get("/")
    async def root():
        """根路径"""
        return {
            "message": "量化交易系统API",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }
    
    @app.get("/api/health")
    async def health_check():
        """健康检查"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }
    
    logger.info("FastAPI应用已创建")
    return app

