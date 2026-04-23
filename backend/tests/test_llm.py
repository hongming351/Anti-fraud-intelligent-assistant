#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加父目录到路径以支持导入app模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.llm_risk_judge import LLMRiskJudge

judge = LLMRiskJudge()
result = judge.judge("您的账户异常，需要转账验证身份")
print(result.fraud_type)  # 输出: 冒充官方机构诈骗