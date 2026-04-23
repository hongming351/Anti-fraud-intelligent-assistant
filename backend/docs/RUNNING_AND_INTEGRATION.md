# LLM反诈分析 - 运行和集成指南

## 目录
1. [快速运行](#快速运行)
2. [集成到FastAPI](#集成到fastapi)
3. [API使用示例](#api使用示例)
4. [故障排除](#故障排除)

---

## 快速运行

### 前置条件

```bash
# 安装Python 3.8+
python --version

# 进入项目目录
cd Anti-fraud-intelligent-assistant-1/backend
```

### 方式1：运行演示脚本（推荐新手）

```bash
# 运行完整演示（包含9个演示程序）
python demo_llm_analysis.py

# 或运行特定演示
python -m pytest tests/test_llm_versions.py -v
```

**演示内容**：
```
演示1: 基础分析功能
演示2: 少样本学习提示词（推荐）
演示3: 结构化输出
演示4: 上下文感知分析
演示5: 完整风险判断（带用户角色）
演示6: 提示词版本对比
演示7: 批量分析
演示8: 本地规则降级
演示9: 详细报告生成
```

### 方式2：简单Python脚本

创建 `test_llm.py`：

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.llm_risk_judge import LLMRiskJudge
from app.core.llm_analyzer import PromptVersion

def test_basic():
    """基础测试"""
    judge = LLMRiskJudge()
    
    test_cases = [
        "您的账户异常，需要立即转账验证身份。",
        "嗨，今天天气不错，我们一起去公园吗？",
        "投资理财项目，年回报率30%，立即加入。"
    ]
    
    for text in test_cases:
        print(f"\n分析: {text[:40]}...")
        result = judge.judge(text)
        print(f"风险等级: {result.risk_level.value}")
        print(f"诈骗类型: {result.fraud_type}")
        print(f"风险分数: {result.risk_score:.1f}")

if __name__ == "__main__":
    test_basic()
```

运行：
```bash
python test_llm.py
```

### 方式3：交互式Python shell

```bash
# 启动Python解释器
python

# 然后在解释器中运行：
>>> from app.core.llm_risk_judge import LLMRiskJudge
>>> judge = LLMRiskJudge()
>>> result = judge.judge("您的账户异常，需要转账。")
>>> print(result.to_json())
```

---

## 集成到FastAPI

### 步骤1：在现有的analyze.py中集成

打开 `backend/app/api/analyze.py`，添加：

```python
# 在文件顶部导入
from ..core.llm_risk_judge import LLMRiskJudge
from ..core.llm_analyzer import PromptVersion

# 创建实例
llm_judge = LLMRiskJudge()

# 添加新的路由
@router.post("/text/deep", response_model=schemas.AnalysisResult)
def analyze_text_with_llm(
    request: schemas.TextAnalysisRequest,
    current_user: schemas.UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    使用LLM进行深度文本分析
    
    与普通的analyze_text相比，这个接口使用大模型进行更深入的分析。
    """
    try:
        # 进行LLM分析
        judgment = llm_judge.judge(
            user_content=request.text,
            user_role=current_user.role.value,
            prompt_version=PromptVersion.V2_EXAMPLES
        )
        
        # 将结果转换为现有的响应格式
        return {
            "risk_level": judgment.risk_level.value,
            "risk_score": judgment.risk_score,
            "fraud_type": judgment.fraud_type,
            "confidence": judgment.confidence,
            "details": str({"reasons": judgment.reasons}),
            "advice": judgment.advice
        }
    except Exception as e:
        logger.error(f"LLM分析失败: {e}")
        # 降级到本地规则
        return analyze_text(request, current_user, db)
```

### 步骤2：单独的LLM API模块

或者创建单独的模块 `backend/app/api/analyze_llm.py`（已提供），然后在主应用中注册：

编辑 `backend/app/main.py`：

```python
# 在包含路由的部分添加
from .api import analyze_llm

# 注册路由
app.include_router(
    analyze_llm.router,
    prefix=settings.API_V1_PREFIX,
    tags=["LLM分析"]
)
```

### 步骤3：启动FastAPI应用

```bash
# 启动开发服务器
cd backend
python run.py

# 或使用uvicorn
uvicorn app.main:app --reload --port 8000
```

访问：
- API文档：http://localhost:8000/docs
- ReDoc：http://localhost:8000/redoc

---

## API使用示例

### 示例1：基础分析

```bash
curl -X POST "http://localhost:8000/api/v1/analyze-llm/text" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "text": "您的账户异常，需要立即转账验证身份。",
    "enable_examples": true,
    "include_similar_cases": true
  }'
```

**响应**：
```json
{
  "risk_level": "高",
  "fraud_type": "冒充公检法诈骗",
  "risk_score": 95,
  "confidence": 0.95,
  "reasons": [
    "冒充公检法部门",
    "要求立即转账",
    "声称账户异常"
  ],
  "warning_keywords": ["账户异常", "转账", "立即"],
  "advice": "这是典型的冒充公检法诈骗。正规的执法部门不会通过网络要求转账。请立即停止，向96110反诈专线报警。"
}
```

### 示例2：批量分析

```bash
curl -X POST "http://localhost:8000/api/v1/analyze-llm/batch" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "requests": [
      {"text": "文本1", "enable_examples": true},
      {"text": "文本2", "enable_examples": true},
      {"text": "文本3", "enable_examples": true}
    ]
  }'
```

### 示例3：Python客户端

```python
import requests
import json

# API配置
BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "your_jwt_token"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}"
}

def analyze_text(text: str) -> dict:
    """调用LLM分析API"""
    response = requests.post(
        f"{BASE_URL}/analyze-llm/text",
        headers=HEADERS,
        json={
            "text": text,
            "enable_examples": True,
            "include_similar_cases": True
        }
    )
    return response.json()

# 使用
result = analyze_text("您的账户异常，需要立即转账验证身份。")
print(json.dumps(result, ensure_ascii=False, indent=2))
```

### 示例4：JavaScript/前端

```javascript
async function analyzeFraud(text, token) {
    const response = await fetch('/api/v1/analyze-llm/text', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            text: text,
            enable_examples: true,
            include_similar_cases: true
        })
    });
    
    const result = await response.json();
    return result;
}

// 使用
const verdict = await analyzeFraud("疑似诈骗文本", token);
console.log(`风险等级: ${verdict.risk_level}`);
console.log(`建议: ${verdict.advice}`);
```

---

## 配置

### 环境变量 (.env)

```env
# LLM配置
LLM_API_KEY=your-api-key-here
LLM_MODEL=gpt-4  # 或其他支持的模型

# 可选：OpenAI API endpoint（如果使用代理）
OPENAI_API_BASE=https://api.openai.com/v1

# 日志级别
LOG_LEVEL=INFO

# 缓存配置
CACHE_ENABLED=true
CACHE_TTL=3600  # 1小时
```

### Python模块配置

在 `backend/app/config.py` 中添加：

```python
class Settings(BaseSettings):
    # ... 现有配置 ...
    
    # LLM配置
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    LLM_API_TIMEOUT: int = 30  # 秒
    LLM_CACHE_ENABLED: bool = True
    
    class Config:
        env_file = ".env"
```

---

## 故障排除

### 问题1：ImportError

```
ImportError: No module named 'app.core.llm_analyzer'
```

**解决**：
```bash
# 确保在正确的目录
cd backend

# 确保app是包
ls app/__init__.py  # 应该存在

# 尝试添加到PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python test_llm.py
```

### 问题2：API密钥错误

```
AuthenticationError: Invalid API key provided
```

**解决**：
```python
# 检查密钥
import os
print(f"API Key: {os.getenv('LLM_API_KEY', 'NOT SET')}")

# 或者在代码中显式设置
from app.core.llm_analyzer import LLMAnalyzer
analyzer = LLMAnalyzer(api_key="your-real-key")
```

### 问题3：超时错误

```
TimeoutError: Request timed out after 30 seconds
```

**解决**：
```python
# 增加超时时间
analyzer = LLMAnalyzer()
analyzer.llm_analyzer.timeout = 60  # 60秒

# 或使用本地规则降级
result = judge.judge_with_local_rules(text)
```

### 问题4：JSON解析错误

```
JSONDecodeError: Expecting value
```

**解决**：
```python
# 启用调试模式查看原始响应
import logging
logging.basicConfig(level=logging.DEBUG)

result = judge.judge(text)
print(result.llm_analysis)  # 查看原始LLM响应
```

### 问题5：内存不足

```
MemoryError: Unable to allocate memory
```

**解决**：
```python
# 使用批处理而不是一次性处理所有数据
for batch in batches(texts, size=10):
    results = analyzer.batch_analyze(batch)
    # 处理结果
    save_results(results)
```

---

## 性能优化

### 1. 启用缓存

```python
from app.core.llm_risk_judge import LLMRiskJudge
from functools import lru_cache

judge = LLMRiskJudge()

@lru_cache(maxsize=1000)
def cached_judge(text: str, role: str):
    """缓存分析结果"""
    return judge.judge(text, user_role=role).to_json()
```

### 2. 异步处理

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

async def analyze_async(text: str):
    """异步分析"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        executor,
        lambda: judge.judge(text)
    )

# 使用
result = await analyze_async("文本")
```

### 3. 批量处理

```python
# 一次性分析多个文本，而不是逐个
texts = ["文本1", "文本2", "文本3", ...]
results = analyzer.batch_analyze(texts)
```

---

## 监控和日志

### 启用详细日志

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 现在会看到详细的日志输出
result = judge.judge("文本")
```

### 监控API调用

```python
import time

def monitor_judge(text: str, role: str = "adult"):
    """监控分析性能"""
    start = time.time()
    result = judge.judge(text, user_role=role)
    elapsed = time.time() - start
    
    print(f"分析耗时: {elapsed:.2f}秒")
    print(f"风险等级: {result.risk_level.value}")
    print(f"API调用数: {1 if result.llm_analysis else 0}")
    
    return result
```

---

## 下一步

1. ✅ 运行演示脚本完成测试
2. ✅ 配置API密钥（可选）
3. ✅ 集成到FastAPI应用
4. ✅ 部署到生产环境
5. ✅ 监控和优化

---

## 参考资源

- [完整使用指南](README_LLM.md)
- [快速参考](QUICK_START_LLM.md)
- [提示词优化指南](PROMPT_ENGINEERING_GUIDE.md)
- [实现总结](IMPLEMENTATION_SUMMARY.md)

---

## 支持

如有问题，请：
1. 检查日志输出
2. 查看故障排除部分
3. 参考相关文档
4. 运行演示脚本

祝你使用愉快！🎉
