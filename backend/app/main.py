from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import os

from .config import settings
from .database import init_db
from .api import auth, analyze, admin

# 配置日志
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("启动反诈智能助手后端服务...")
    
    # 初始化数据库
    try:
        init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise
    
    # 确保上传目录存在
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "audio"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "image"), exist_ok=True)
    logger.info(f"上传目录已创建: {settings.UPLOAD_DIR}")
    
    logger.info(f"服务已启动，访问 http://localhost:8000/docs 查看API文档")
    
    yield  # 应用运行期间
    
    # 关闭时执行
    logger.info("关闭反诈智能助手后端服务...")


# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    docs_url=settings.DOCS_URL if settings.DEBUG else None,
    redoc_url=settings.REDOC_URL if settings.DEBUG else None,
    openapi_url=settings.OPENAPI_URL if settings.DEBUG else None,
    lifespan=lifespan,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件（上传的文件）
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# 包含路由
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(analyze.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用反诈智能助手后端API",
        "project": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "docs": f"访问 {settings.API_V1_PREFIX}/docs 查看API文档",
        "status": "运行正常"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION
    }


@app.get("/info")
async def get_info():
    """获取服务信息"""
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "debug": settings.DEBUG,
        "api_prefix": settings.API_V1_PREFIX,
        "database": "SQLite" if "sqlite" in settings.DATABASE_URL else "PostgreSQL",
        "max_upload_size": f"{settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB",
        "features": [
            "用户认证 (JWT)",
            "文本诈骗分析",
            "音频诈骗分析",
            "图像诈骗分析", 
            "多模态融合分析",
            "风险评估与预警",
            "分析历史记录",
            "文件上传处理"
        ]
    }