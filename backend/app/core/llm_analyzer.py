"""
大模型诈骗检测分析器
集成大模型API进行深度风险评估
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
import os
import re

logger = logging.getLogger(__name__)


class PromptVersion(str, Enum):
    """提示词版本"""
    V1_BASIC = "v1_basic"  # 基础版本
    V2_EXAMPLES = "v2_examples"  # 带少样本学习
    V3_STRUCTURED = "v3_structured"  # 结构化输出
    V4_CONTEXTUAL = "v4_contextual"  # 上下文感知


class LLMAnalyzer:
    """大模型分析器"""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "qwen-turbo"):
        """
        初始化LLM分析器
        
        Args:
            api_key: API密钥，如果为None则从环境变量获取
            model_name: 模型名称，默认qwen-turbo
        """
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.model_name = model_name
        self.prompt_templates = self._load_prompt_templates()
        logger.info(f"LLM分析器初始化完成，模型: {model_name}")
    
    def _load_prompt_templates(self) -> Dict[PromptVersion, str]:
        """加载所有版本的提示词模板"""
        return {
            PromptVersion.V1_BASIC: self._get_basic_prompt(),
            PromptVersion.V2_EXAMPLES: self._get_examples_prompt(),
            PromptVersion.V3_STRUCTURED: self._get_structured_prompt(),
            PromptVersion.V4_CONTEXTUAL: self._get_contextual_prompt(),
        }
    
    def _get_basic_prompt(self) -> str:
        """基础版本提示词"""
        return """你是一位资深的反诈专家，拥有20年的反诈经验。你的职责是分析用户提供的文本内容，判断其中是否存在诈骗风险。

请以JSON格式返回你的分析结果，包含以下字段：
{{
    "fraud_type": "诈骗类型",
    "risk_level": "风险等级（低/中/高）",
    "risk_score": 0-100的数字分数,
    "confidence": 0-1之间的置信度,
    "reasons": ["原因1", "原因2", ...],
    "warning_keywords": ["关键词1", "关键词2", ...],
    "advice": "建议文案"
}}

分析时请考虑以下方面：
1. 识别常见的诈骗模式（冒充公检法、投资理财、钓鱼、购物退款、杀猪盘、贷款、赌博等）
2. 识别紧急警告词（转账、验证码、安全账户、涉嫌洗钱等）
3. 分析文本的紧迫性和操作压力
4. 评估信息的可信度

现在请分析以下内容：

用户内容：
{user_content}

相似的诈骗案例参考：
{similar_cases}

请以JSON格式直接返回分析结果，不要包含其他说明文字。"""
    
    def _get_examples_prompt(self) -> str:
        """带少样本学习的提示词（2个示例）"""
        return """你是一位资深的反诈专家，拥有20年的反诈经验。你的职责是分析用户提供的文本内容，判断其中是否存在诈骗风险。

请以JSON格式返回你的分析结果。参考以下示例：

示例1（高风险-冒充公检法诈骗）：
用户内容："你好，我是市公安局的。经查证，你的两张银行卡涉嫌洗钱，需要立即转账到安全账户进行资金冻结..."
返回结果：
{{
    "fraud_type": "冒充公检法诈骗",
    "risk_level": "高",
    "risk_score": 95,
    "confidence": 0.98,
    "reasons": [
        "冒充政府部门（公安局）",
        "虚构犯罪指控（涉嫌洗钱）",
        "要求转账到陌生账户（安全账户）",
        "使用紧急和恐吓语言（立即转账）"
    ],
    "warning_keywords": ["公安局", "涉嫌洗钱", "安全账户", "立即转账"],
    "advice": "这是典型的冒充公检法诈骗。正规的执法部门不会通过微信/电话要求转账。请立即停止，向96110反诈专线报警。"
}}

示例2（低风险-正常交流）：
用户内容："嗨，今天天气真好，我们下午去公园散步吧？"
返回结果：
{{
    "fraud_type": "无",
    "risk_level": "低",
    "risk_score": 5,
    "confidence": 0.95,
    "reasons": [
        "日常闲聊内容",
        "无经济交易建议",
        "无紧急操作要求",
        "无可疑链接或账号要求"
    ],
    "warning_keywords": [],
    "advice": "未检测到明显诈骗迹象，但仍需保持防范意识。"
}}

现在请分析以下内容，返回格式同上：

用户内容：
{user_content}

相似的诈骗案例参考：
{similar_cases}

请以JSON格式直接返回分析结果，不要包含其他说明文字。"""
    
    def _get_structured_prompt(self) -> str:
        """结构化输出提示词"""
        return """你是一位资深的反诈专家，拥有20年的反诈经验。你的职责是精确分析用户提供的文本内容，判断其中是否存在诈骗风险。

请严格按照以下JSON Schema返回分析结果：
{{
    "fraud_type": "诈骗类型（必选值：冒充公检法诈骗、投资理财诈骗、钓鱼诈骗、购物退款诈骗、杀猪盘诈骗、贷款诈骗、赌博诈骗、可疑交易、无）",
    "risk_level": "风险等级（必选值：低、中、高）",
    "risk_score": "0-100的整数",
    "confidence": "0-100的整数（置信度百分比）",
    "reasons": ["原因1", "原因2", "原因3"],
    "warning_keywords": ["关键词1", "关键词2", "关键词3"],
    "fraud_indicators": {{
        "urgency": "紧迫性水平（低/中/高）",
        "financial_request": "是否涉及财务请求（是/否）",
        "identity_claim": "是否冒充身份（是/否）",
        "trust_exploitation": "是否利用信任关系（是/否）"
    }},
    "advice": "针对性建议文案（30-100字）"
}}

分析标准：
1. 高风险（75-100）：包含明确的诈骗特征，如冒充身份、紧迫的财务要求、链接/验证码请求
2. 中风险（40-74）：包含可疑特征但不确定，如模糊的投资承诺、异常活动通知
3. 低风险（0-39）：日常交流、正常客服、无诈骗迹象

用户内容：
{user_content}

相似的诈骗案例参考：
{similar_cases}

返回有效的JSON格式，确保所有字段都存在且类型正确。"""
    
    def _get_contextual_prompt(self) -> str:
        """上下文感知提示词（最优版本）"""
        return """你是一位资深的反诈专家，拥有20年的反诈经验。你的职责是根据上下文和用户信息，精确分析文本内容的诈骗风险。

【关键诈骗类型特征库】
1. 冒充公检法：要求转账到"安全账户"、虚构犯罪指控、使用官方身份
2. 投资理财：承诺高回报、要求投入资金、提供内幕消息
3. 钓鱼诈骗：要求点击链接、索要验证码、账户异常警告
4. 购物退款：声称退款需要补充信息、要求转账到私人账户
5. 杀猪盘：建立信任后诱导投资、需要"见面"或"解决困难"
6. 贷款诈骗：声称无抵押快速贷款、要求前期费用
7. 赌博诈骗：邀请参与博彩、承诺稳定暴利

【上下文因素】
根据以下信息增强判断准确性：
- 相似案例的通用特征
- 文本中的紧迫性语言
- 涉及的金额或数字
- 对方的身份声称

请返回以下JSON格式的分析结果：
{{
    "fraud_type": "具体诈骗类型或'无'",
    "risk_level": "低/中/高",
    "risk_score": 0-100,
    "confidence": 0-100,
    "analysis": {{
        "detected_patterns": ["模式1", "模式2"],
        "suspicious_phrases": ["短语1", "短语2"],
        "urgency_indicators": ["指标1", "指标2"],
        "trust_exploitations": ["利用1", "利用2"]
    }},
    "reasons": ["原因1", "原因2", "原因3", "原因4"],
    "warning_keywords": ["关键词1", "关键词2", "关键词3"],
    "advice": "根据风险等级给出针对性建议，包含具体行动步骤"
}}

用户内容：
{user_content}

相似的诈骗案例参考（提供高价值参考）：
{similar_cases}

请返回精确的JSON格式的分析结果。"""
    
    def analyze_with_llm(
        self,
        user_content: str,
        similar_cases: Optional[List[Dict]] = None,
        prompt_version: PromptVersion = PromptVersion.V2_EXAMPLES
    ) -> Dict:
        """
        使用大模型进行分析
        
        Args:
            user_content: 用户输入的文本
            similar_cases: 检索到的相似诈骗案例
            prompt_version: 使用的提示词版本
        
        Returns:
            分析结果字典
        """
        try:
            # 构建提示词
            similar_cases_text = self._format_similar_cases(similar_cases)
            prompt = self.prompt_templates[prompt_version]
            message_content = prompt.format(
                # 对内容进行转义，防止其中包含的 { } 破坏 .format() 逻辑
                user_content=user_content.replace("{", "{{").replace("}", "}}"),
                similar_cases=similar_cases_text.replace("{", "{{").replace("}", "}}")
            )
            
            # 调用大模型API
            response = self._call_llm_api(message_content)
            
            # 解析响应
            result = self._parse_llm_response(response)
            result["prompt_version"] = prompt_version.value
            
            return result
        except Exception as e:
            logger.error(f"LLM分析失败: {e}")
            return self._get_fallback_result(user_content)
    
    def _format_similar_cases(self, similar_cases: Optional[List[Dict]]) -> str:
        """格式化相似案例"""
        if not similar_cases:
            return "暂无相似案例参考"
        
        formatted = []
        for i, case in enumerate(similar_cases[:3], 1):  # 最多显示3个
            case_text = f"案例{i}: {case.get('description', case.get('content', ''))}"
            if case.get('fraud_type'):
                case_text += f" (类型: {case['fraud_type']})"
            if case.get('risk_level'):
                case_text += f" (风险: {case['risk_level']})"
            formatted.append(case_text)
        
        return "\n".join(formatted) if formatted else "暂无相似案例参考"
    
    def _call_llm_api(self, prompt: str) -> str:
        """
        调用LLM API
        
        这是一个接口方法，需要根据实际使用的API服务实现
        支持阿里通义千问、OpenAI、文心一言等API
        """
        # 根据模型名称调用相应的API
        
        # 示例1: 阿里通义千问
        if "qwen" in self.model_name.lower():
            return self._call_qwen_api(prompt)
        
        # 示例2: OpenAI API
        elif self.model_name.startswith("gpt"):
            return self._call_openai_api(prompt)
        
        # 示例3: 百度文心一言
        elif "ernie" in self.model_name.lower():
            return self._call_wenxin_api(prompt)
        
        # 默认返回模拟结果
        logger.warning("未配置真实API，使用本地模拟结果")
        return self._get_mock_response(prompt)
    
    def _call_openai_api(self, prompt: str) -> str:
        """调用OpenAI API"""
        try:
            import openai
            openai.api_key = self.api_key
            
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位资深的反诈专家。请以JSON格式返回分析结果。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # 降低温度以获得更一致的结果
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            raise
    
    def _call_qwen_api(self, prompt: str) -> str:
        """调用阿里通义千问API"""
        try:
            # 验证API密钥是否正确设置
            if not self.api_key or self.api_key == "":
                raise ValueError("API密钥未设置。请检查 .env 文件中的 LLM_API_KEY")
            
            from dashscope import Generation
            
            logger.info(f"调用千问API - 模型: {self.model_name}")
            
            # 直接使用 DashScope SDK
            response = Generation.call(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位资深的反诈专家。请以JSON格式返回分析结果。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                api_key=self.api_key,
                temperature=0.3,
                top_p=0.8
            )
            
            if response.status_code == 200:
                logger.info("千问API调用成功")
                return response.output.text
            else:
                logger.error(f"千问API返回错误状态码: {response.status_code}")
                raise Exception(f"API错误: {response.message}")
            
        except Exception as e:
            logger.error(f"通义千问API调用失败: {e}")
            raise
    
    def _call_wenxin_api(self, prompt: str) -> str:
        """调用百度文心一言API"""
        try:
            import requests
            
            url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie"
            headers = {"Content-Type": "application/json"}
            
            # 需要先获取access token
            access_token = self._get_baidu_access_token()
            
            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "top_p": 0.8,
                "top_k": 0
            }
            
            response = requests.post(
                f"{url}?access_token={access_token}",
                json=payload,
                headers=headers
            )
            
            result = response.json()
            if response.status_code == 200:
                return result.get("result", {}).get("message", "")
            else:
                raise Exception(f"API返回错误: {result}")
        except Exception as e:
            logger.error(f"文心一言API调用失败: {e}")
            raise
    
    def _get_baidu_access_token(self) -> str:
        """获取百度API的access token"""
        # TODO: 实现从环境变量或配置获取client_id和client_secret
        pass
    
    def _parse_llm_response(self, response: str) -> Dict:
        """
        解析大模型的响应
        
        Args:
            response: 原始响应文本
        
        Returns:
            规范化的结果字典
        """
        try:
            # 尝试提取JSON部分
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
            else:
                raise ValueError("响应中找不到JSON")
            
            # 规范化字段
            normalized = self._normalize_llm_result(data)
            return normalized
        except Exception as e:
            logger.error(f"解析LLM响应失败: {e}, 原始响应: {response}")
            return self._get_fallback_result("")
    
    def _normalize_llm_result(self, data: Dict) -> Dict:
        """
        规范化LLM返回的结果
        
        确保所有字段都存在并且格式正确
        """
        # 标准化风险等级
        risk_level = str(data.get("risk_level", "低")).lower().strip()
        if risk_level not in ["低", "中", "高"]:
            risk_level = self._infer_risk_level(data.get("risk_score", 0))
        
        # 标准化风险分数
        risk_score = float(data.get("risk_score", 0))
        if risk_score < 0:
            risk_score = 0
        elif risk_score > 100:
            risk_score = 100
        
        # 标准化置信度
        confidence = float(data.get("confidence", 0.5))
        if confidence > 1:
            confidence = confidence / 100
        confidence = max(0, min(1, confidence))
        
        # 诈骗类型
        fraud_type = str(data.get("fraud_type", "可疑交易")).strip()
        
        # 原因列表
        reasons = data.get("reasons", [])
        if isinstance(reasons, str):
            reasons = [reasons]
        reasons = [str(r).strip() for r in reasons if r][:5]  # 最多5个原因
        
        # 警告关键词
        warning_keywords = data.get("warning_keywords", [])
        if isinstance(warning_keywords, str):
            warning_keywords = [warning_keywords]
        warning_keywords = [str(k).strip() for k in warning_keywords if k][:5]
        
        # 建议
        advice = str(data.get("advice", "请保持警惕")).strip()
        
        return {
            "fraud_type": fraud_type,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "confidence": confidence,
            "reasons": reasons,
            "warning_keywords": warning_keywords,
            "advice": advice,
            "raw_response": data  # 保存原始响应用于调试
        }
    
    def _infer_risk_level(self, risk_score: float) -> str:
        """根据分数推断风险等级"""
        if risk_score >= 60:
            return "高"
        elif risk_score >= 30:
            return "中"
        else:
            return "低"
    
    def _get_mock_response(self, prompt: str) -> str:
        """
        获取本地模拟响应
        用于测试和演示，当API不可用时使用
        """
        # 根据关键词进行简单的本地判断
        keywords_high = ["公安局", "检察院", "法院", "安全账户", "涉嫌", "转账", "验证码", "冻结"]
        keywords_medium = ["投资", "理财", "高回报", "退款", "客服", "链接", "确认"]
        
        has_high = any(kw in prompt for kw in keywords_high)
        has_medium = any(kw in prompt for kw in keywords_medium)
        
        if has_high:
            risk_level = "高"
            risk_score = 85
        elif has_medium:
            risk_level = "中"
            risk_score = 55
        else:
            risk_level = "低"
            risk_score = 15
        
        mock_response = {
            "fraud_type": "冒充公检法诈骗" if has_high else ("投资理财诈骗" if has_medium else "无"),
            "risk_level": risk_level,
            "risk_score": risk_score,
            "confidence": 0.8 if has_high else (0.6 if has_medium else 0.9),
            "reasons": ["基于本地规则判断"],
            "warning_keywords": [kw for kw in keywords_high if kw in prompt],
            "advice": "这是本地模拟结果，建议配置API服务以获得更准确的判断。"
        }
        
        return json.dumps(mock_response, ensure_ascii=False)
    
    def _get_fallback_result(self, content: str) -> Dict:
        """获取降级方案结果"""
        return {
            "fraud_type": "无法判断",
            "risk_level": "中",
            "risk_score": 50,
            "confidence": 0.3,
            "reasons": ["LLM分析失败，使用降级方案"],
            "warning_keywords": [],
            "advice": "由于分析服务异常，建议您保持警惕并向平台举报可疑内容。"
        }
    
    def batch_analyze(
        self,
        contents: List[str],
        similar_cases_list: Optional[List[List[Dict]]] = None,
        prompt_version: PromptVersion = PromptVersion.V2_EXAMPLES
    ) -> List[Dict]:
        """
        批量分析多个内容
        
        Args:
            contents: 内容列表
            similar_cases_list: 对应的相似案例列表
            prompt_version: 提示词版本
        
        Returns:
            分析结果列表
        """
        results = []
        for i, content in enumerate(contents):
            similar_cases = similar_cases_list[i] if similar_cases_list and i < len(similar_cases_list) else None
            result = self.analyze_with_llm(
                user_content=content,
                similar_cases=similar_cases,
                prompt_version=prompt_version
            )
            results.append(result)
        
        return results
    
    def compare_prompt_versions(
        self,
        user_content: str,
        similar_cases: Optional[List[Dict]] = None
    ) -> Dict:
        """
        使用所有版本的提示词进行分析并比较结果
        用于选择最优版本
        
        Args:
            user_content: 用户输入的文本
            similar_cases: 检索到的相似诈骗案例
        
        Returns:
            包含所有版本结果的字典
        """
        results = {}
        for version in PromptVersion:
            try:
                result = self.analyze_with_llm(
                    user_content=user_content,
                    similar_cases=similar_cases,
                    prompt_version=version
                )
                results[version.value] = result
            except Exception as e:
                logger.error(f"版本 {version.value} 分析失败: {e}")
                results[version.value] = {"error": str(e)}
        
        return {
            "user_content": user_content,
            "versions": results,
            "recommendation": self._recommend_best_version(results)
        }
    
    def _recommend_best_version(self, results: Dict) -> str:
        """
        推荐最佳的提示词版本
        基于置信度和分析准确性
        """
        best_version = None
        best_score = 0
        
        for version, result in results.items():
            if "error" in result:
                continue
            
            # 计算分数：置信度 + 原因数量
            score = (result.get("confidence", 0) * 100 + 
                    len(result.get("reasons", [])) * 10)
            
            if score > best_score:
                best_score = score
                best_version = version
        
        return best_version or "v2_examples"


# 创建全局实例
llm_analyzer = LLMAnalyzer()
