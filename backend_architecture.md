# 反诈智能助手后端架构设计

## 1. 技术栈选择

### 后端框架

- **FastAPI**: 高性能异步框架，适合实时AI分析场景
- **SQLAlchemy**: ORM框架，支持多种数据库
- **Pydantic**: 数据验证和序列化

### 数据库

- **SQLite** (开发环境): 轻量级，便于快速开发
- **PostgreSQL** (生产环境): 支持复杂查询和事务

### AI/ML组件

- **Transformers** (Hugging Face): 预训练模型用于文本分析
- **SpeechRecognition**: 语音转文本
- **OpenCV/Pillow**: 图像处理
- **scikit-learn**: 传统机器学习模型

### 其他工具

- **Celery**: 异步任务队列（用于耗时分析任务）
- **Redis**: 缓存和消息代理
- **JWT**: 用户认证
- **Uvicorn**: ASGI服务器

## 2. 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  前端 (Streamlit) │───▶│   API Gateway   │───▶│  业务逻辑层     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                      │
                                                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   文件存储       │◀───│   AI分析引擎    │◀───│  数据访问层     │
│   (MinIO/S3)    │    └─────────────────┘    └─────────────────┘
└─────────────────┘           │                       │
                              ▼                       ▼
                     ┌─────────────────┐    ┌─────────────────┐
                     │  模型服务       │    │  数据库         │
                     │  (TensorFlow)   │    │  (PostgreSQL)   │
                     └─────────────────┘    └─────────────────┘
```

## 3. 核心模块设计

### 3.1 用户管理模块

- 用户注册/登录
- 角色管理（儿童、青年、中年、老年人、高风险人群）
- 监护人信息管理
- 用户偏好设置

### 3.2 多模态分析模块

#### 文本分析子模块

- 关键词匹配（规则引擎）
- NLP情感分析
- 意图识别
- 相似度匹配（与已知诈骗模式对比）

#### 语音分析子模块

- 语音转文本（STT）
- 声纹分析
- 情感识别
- 深度伪造检测

#### 图像分析子模块

- OCR文字提取
- 二维码检测
- 场景识别
- 人脸检测（隐私保护）

### 3.3 风险评估模块

- 多模态融合评分
- 风险等级划分（低危、中危、高危）
- 置信度计算
- 实时预警机制

### 3.4 报告生成模块

- 分析报告生成
- 历史记录查询
- 数据可视化
- CSV/PDF导出

### 3.5 知识库管理模块

- 诈骗模式库
- 案例库
- 关键词库
- 自适应学习机制

## 4. API接口设计

### 4.1 认证相关

- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/refresh` - 刷新令牌
- `GET /api/auth/profile` - 获取用户信息

### 4.2 分析相关

- `POST /api/analyze/text` - 文本分析
- `POST /api/analyze/audio` - 语音分析
- `POST /api/analyze/image` - 图像分析
- `POST /api/analyze/multimodal` - 多模态融合分析

### 4.3 报告相关

- `GET /api/reports` - 获取分析历史
- `GET /api/reports/{report_id}` - 获取详细报告
- `POST /api/reports/export` - 导出报告
- `GET /api/reports/statistics` - 获取统计数据

### 4.4 管理相关

- `GET /api/admin/patterns` - 获取诈骗模式
- `POST /api/admin/patterns` - 添加诈骗模式
- `PUT /api/admin/patterns/{pattern_id}` - 更新诈骗模式
- `GET /api/admin/analytics` - 系统分析数据

## 5. 数据库设计

### 5.1 用户表 (users)

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,  -- 'child', 'youth', 'adult', 'elderly', 'high_risk'
    gender VARCHAR(10),
    risk_sensitivity VARCHAR(10) DEFAULT 'medium',
    guardian_name VARCHAR(100),
    guardian_phone VARCHAR(20),
    guardian_email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5.2 分析记录表 (analysis_records)

```sql
CREATE TABLE analysis_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    analysis_type VARCHAR(20) NOT NULL,  -- 'text', 'audio', 'image', 'multimodal'
    input_text TEXT,
    audio_file_path VARCHAR(255),
    image_file_path VARCHAR(255),
    risk_level VARCHAR(10) NOT NULL,  -- 'low', 'medium', 'high'
    risk_score FLOAT NOT NULL,
    fraud_type VARCHAR(100),
    confidence FLOAT NOT NULL,
    details TEXT,
    advice TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 5.3 诈骗模式表 (fraud_patterns)

```sql
CREATE TABLE fraud_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_type VARCHAR(50) NOT NULL,  -- 'impersonation', 'investment', 'phishing', etc.
    keywords TEXT NOT NULL,
    description TEXT,
    risk_weight FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5.4 预警记录表 (alerts)

```sql
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    analysis_record_id INTEGER NOT NULL,
    alert_level VARCHAR(10) NOT NULL,  -- 'low', 'medium', 'high'
    action_taken VARCHAR(100),  -- 'blocked', 'notified', 'reported'
    notified_guardian BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (analysis_record_id) REFERENCES analysis_records(id)
);
```

## 6. 文件结构

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
│   ├── security.py          # 安全相关（JWT、密码哈希）
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py          # 认证路由
│   │   ├── analyze.py       # 分析路由
│   │   ├── reports.py       # 报告路由
│   │   └── admin.py         # 管理路由
│   ├── core/
│   │   ├── __init__.py
│   │   ├── text_analyzer.py     # 文本分析
│   │   ├── audio_analyzer.py    # 语音分析
│   │   ├── image_analyzer.py    # 图像分析
│   │   ├── risk_assessor.py     # 风险评估
│   │   └── report_generator.py  # 报告生成
│   ├── services/
│   │   ├── __init__.py
│   │   ├── file_service.py      # 文件上传处理
│   │   ├── ai_service.py        # AI模型服务
│   │   └── notification_service.py # 通知服务
│   └── utils/
│       ├── __init__.py
│       ├── logger.py         # 日志配置
│       └── helpers.py        # 工具函数
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   └── test_models.py
├── uploads/                  # 上传文件目录
├── models/                   # 预训练模型目录
├── requirements.txt
├── .env.example
└── README.md
```

## 7. 部署配置

### 开发环境

```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/antifraud_dev
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=antifraud_dev
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
  
  celery:
    build: .
    command: celery -A app.celery_app worker --loglevel=info
    depends_on:
      - redis
      - db

volumes:
  postgres_data:
```

## 8. 下一步实施计划

1. **第一阶段**: 基础框架搭建
   - 创建FastAPI项目结构
   - 配置数据库和ORM
   - 实现用户认证系统

2. **第二阶段**: 核心分析功能
   - 实现文本分析模块
   - 实现语音分析模块（基础STT）
   - 实现图像分析模块（基础OCR）

3. **第三阶段**: 高级功能
   - 多模态融合分析
   - 风险评估引擎
   - 报告生成系统

4. **第四阶段**: 集成与优化
   - 前后端集成
   - 性能优化
   - 安全加固

5. **第五阶段**: 部署与监控
   - 容器化部署
   - 监控和日志
   - 自动化测试
