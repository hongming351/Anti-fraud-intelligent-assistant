# 反诈智能助手后端

基于FastAPI的多模态反诈分析后端系统，支持文本、语音、图像多模态诈骗检测。

## 功能特性

- **用户管理**: 用户注册、登录、个人信息管理
- **多模态分析**: 
  - 文本诈骗分析（关键词匹配、深度分析）
  - 音频诈骗分析（语音识别、声纹分析）
  - 图像诈骗分析（OCR识别、场景分析）
  - 多模态融合分析
- **风险评估**: 智能风险评分、等级划分、处置建议
- **预警系统**: 实时预警、监护人联动
- **报告生成**: 分析历史、统计报表、数据导出
- **知识库管理**: 诈骗模式库、自适应学习

## 技术栈

- **后端框架**: FastAPI (Python 3.8+)
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **ORM**: SQLAlchemy
- **认证**: JWT (JSON Web Tokens)
- **文件处理**: Python-Multipart
- **AI/ML**: Transformers, OpenCV, SpeechRecognition
- **异步任务**: Celery + Redis (可选)
- **API文档**: Swagger UI (自动生成)

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制环境变量示例文件并修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，根据需要修改配置：

```env
# 数据库配置
DATABASE_URL=sqlite:///./antifraud.db

# JWT配置
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 文件上传配置
MAX_UPLOAD_SIZE=10485760  # 10MB
```

### 3. 启动服务

```bash
# 方式1: 使用启动脚本
python run.py

# 方式2: 直接使用uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后，访问以下地址：
- API文档: http://localhost:8000/api/v1/docs
- 服务状态: http://localhost:8000/health

## API接口

### 认证相关
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/auth/profile` - 获取用户信息
- `PUT /api/v1/auth/profile` - 更新用户信息

### 分析相关
- `POST /api/v1/analyze/text` - 文本分析
- `POST /api/v1/analyze/audio` - 音频分析
- `POST /api/v1/analyze/image` - 图像分析
- `POST /api/v1/analyze/multimodal` - 多模态融合分析
- `GET /api/v1/analyze/history` - 获取分析历史

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI应用入口
│   ├── config.py            # 配置文件
│   ├── database.py          # 数据库连接
│   ├── models.py            # SQLAlchemy模型
│   ├── schemas.py           # Pydantic模型
│   ├── crud.py              # 数据库操作
│   ├── dependencies.py      # 依赖注入
│   ├── security.py          # 安全相关
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py          # 认证路由
│   │   └── analyze.py       # 分析路由
│   ├── core/
│   │   ├── __init__.py
│   │   ├── text_analyzer.py     # 文本分析
│   │   └── risk_assessor.py     # 风险评估
│   └── utils/
│       └── __init__.py
├── tests/                   # 测试文件
├── uploads/                 # 上传文件目录
├── requirements.txt         # Python依赖
├── .env.example            # 环境变量示例
├── run.py                  # 启动脚本
└── README.md               # 本文档
```

## 数据库设计

### 主要数据表

1. **users** - 用户表
   - id, username, email, password_hash
   - role, gender, risk_sensitivity
   - guardian_name, guardian_phone, guardian_email

2. **analysis_records** - 分析记录表
   - id, user_id, analysis_type
   - input_text, audio_file_path, image_file_path
   - risk_level, risk_score, fraud_type, confidence
   - details, advice, created_at

3. **fraud_patterns** - 诈骗模式表
   - id, pattern_type, keywords, description
   - risk_weight, created_at, updated_at

4. **alerts** - 预警记录表
   - id, user_id, analysis_record_id
   - alert_level, action_taken, notified_guardian
   - created_at

## 开发指南

### 添加新的API路由

1. 在 `app/api/` 目录下创建新的路由文件
2. 在 `app/main.py` 中导入并包含路由
3. 在 `app/schemas.py` 中定义相关的Pydantic模型

### 添加新的分析模块

1. 在 `app/core/` 目录下创建新的分析器类
2. 实现分析逻辑和结果生成
3. 在相应的API路由中调用分析器

### 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio httpx

# 运行测试
pytest tests/
```

## 部署

### 生产环境配置

1. 修改 `.env` 文件中的配置：
   - 使用PostgreSQL数据库
   - 设置强密码的SECRET_KEY
   - 关闭DEBUG模式
   - 配置合适的CORS域名

2. 使用Gunicorn运行（推荐）：
```bash
pip install gunicorn
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

3. 使用Docker部署：
```bash
# 构建镜像
docker build -t antifraud-backend .

# 运行容器
docker run -d -p 8000:8000 --name antifraud-backend antifraud-backend
```

### 监控与日志

- 访问 `/health` 端点进行健康检查
- 查看应用日志了解运行状态
- 使用Prometheus + Grafana进行监控（可选）

## 注意事项

1. **安全性**:
   - 生产环境务必修改默认的SECRET_KEY
   - 启用HTTPS加密传输
   - 限制文件上传大小和类型
   - 实施速率限制防止滥用

2. **性能**:
   - 对于大文件分析，建议使用异步任务队列
   - 启用数据库连接池
   - 使用缓存提高响应速度

3. **扩展性**:
   - 支持分布式部署
   - 可集成第三方AI服务
   - 支持插件式分析模块

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查DATABASE_URL配置
   - 确保数据库服务正常运行
   - 检查文件权限（SQLite）

2. **文件上传失败**
   - 检查上传目录权限
   - 验证文件大小限制
   - 检查文件类型白名单

3. **JWT认证失败**
   - 检查SECRET_KEY配置
   - 验证令牌过期时间
   - 检查请求头格式

### 获取帮助

- 查看API文档: http://localhost:8000/api/v1/docs
- 检查应用日志
- 提交Issue报告问题

## 许可证

本项目采用MIT许可证。详见LICENSE文件。