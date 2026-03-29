# 多模态反诈智能助手

这是一个完整的反诈应用系统，包含前端（Streamlit）和后端（FastAPI），支持文本、语音、图像多模态分析。

## 项目结构

```
Anti-fraud intelligent assistant/
├── front_end.py              # Streamlit前端界面
├── run.py                   # 前端启动脚本
├── main.py                  # 前端主文件
├── requirements.txt         # 前端依赖
├── README.md               # 项目文档
├── .gitignore              # Git忽略文件
├── backend/                # 后端服务
│   ├── app/               # 后端应用代码
│   ├── requirements.txt   # 后端依赖
│   ├── run.py            # 后端启动脚本
│   ├── README.md         # 后端文档
│   └── .env.example      # 后端环境变量示例
└── backend_architecture.md # 后端架构设计文档
```

## 运行方式

### 前端运行（Streamlit）

1. 安装前端依赖：

   ```bash
   pip install -r requirements.txt
   ```

2. 运行前端应用：

   ```bash
   python run.py
   ```

3. 在浏览器中打开：<http://localhost:8501>

### 后端运行（FastAPI）

1. 进入后端目录：

   ```bash
   cd backend
   ```

2. 安装后端依赖：

   ```bash
   pip install -r requirements.txt
   ```

3. 配置环境变量：

   ```bash
   cp .env.example .env
   # 编辑.env文件，根据需要修改配置
   ```

4. 启动后端服务：

   ```bash
   python run.py
   # 或直接使用：uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. 访问API文档：<http://localhost:8000/api/v1/docs>

### 完整系统运行

1. 启动后端服务（端口8000）
2. 启动前端服务（端口8501）
3. 前端通过API调用后端服务进行分析

## 功能特性

### 前端功能
- 文本分析：支持聊天记录、短信、社交媒体文案分析
- 语音分析：支持通话录音、语音消息分析
- 图像分析：支持屏幕截图、视频截图、图片分析
- 多模态融合：综合分析诈骗风险
- 个性化设置：角色定制、监护人联动
- 实时预警：高危、中危、低危风险分级
- 安全报告：生成CSV格式安全监测报告

### 后端功能
- 用户管理：注册、登录、个人信息管理
- 多模态分析API：文本、音频、图像、多模态融合分析
- 风险评估引擎：智能风险评分、等级划分
- 预警系统：实时预警、监护人联动通知
- 数据持久化：分析记录存储、历史查询
- 诈骗知识库：模式库管理、自适应学习

## 技术栈

### 前端
- Streamlit：前端框架
- Pandas：数据处理
- Python：业务逻辑

### 后端
- FastAPI：高性能异步API框架
- SQLAlchemy：ORM数据库操作
- SQLite/PostgreSQL：数据库存储
- JWT：用户认证
- Pydantic：数据验证
- Transformers/OpenCV/SpeechRecognition：AI分析组件

## 系统架构

### 前端架构
- 用户界面层：Streamlit组件
- 业务逻辑层：分析请求处理
- API通信层：与后端服务交互

### 后端架构
- API网关层：FastAPI路由
- 业务逻辑层：分析引擎、风险评估
- 数据访问层：数据库操作
- AI分析层：多模态分析模块

## 开发指南

### 前端开发
1. 修改 `front_end.py` 文件更新界面
2. 更新 `requirements.txt` 添加新依赖
3. 运行 `python run.py` 测试更改

### 后端开发
1. 进入 `backend` 目录
2. 修改相应模块文件
3. 运行 `python run.py` 测试API
4. 访问 <http://localhost:8000/api/v1/docs> 测试接口

### API集成
前端通过HTTP请求调用后端API：
- 认证：`POST /api/v1/auth/login`
- 文本分析：`POST /api/v1/analyze/text`
- 音频分析：`POST /api/v1/analyze/audio`
- 图像分析：`POST /api/v1/analyze/image`
- 多模态分析：`POST /api/v1/analyze/multimodal`

## 部署说明

### 开发环境
- 使用SQLite数据库
- 启用调试模式
- 允许所有CORS来源

### 生产环境
1. 使用PostgreSQL数据库
2. 设置强密码的SECRET_KEY
3. 配置HTTPS加密
4. 使用Gunicorn运行后端
5. 配置Nginx反向代理

## 注意事项

- 首次运行需要安装所有依赖包
- 建议使用Python 3.8+版本
- 生产环境务必修改默认密钥和配置
- 大文件分析建议使用异步任务队列

## 后续开发计划

1. **AI模型优化**：集成更先进的NLP和CV模型
2. **实时分析**：支持实时流式数据分析
3. **移动端支持**：开发移动应用版本
4. **第三方集成**：对接微信、支付宝等平台
5. **大数据分析**：用户行为分析和模式挖掘

## 许可证

本项目采用MIT许可证。
