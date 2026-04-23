"""
LLM风险判断器
集成大模型分析和本地规则，提供最终的风险判断结果
"""

import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime

from .llm_analyzer import LLMAnalyzer, PromptVersion

logger = logging.getLogger(__name__)


class RiskJudgmentLevel(str, Enum):
    """风险判断等级"""
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"


class JudgmentResult:
    """风险判断结果类"""
    
    def __init__(
        self,
        risk_level: RiskJudgmentLevel,
        fraud_type: str,
        risk_score: float,
        confidence: float,
        reasons: List[str],
        advice: str,
        warning_keywords: Optional[List[str]] = None,
        llm_analysis: Optional[Dict] = None
    ):
        """
        初始化判断结果
        
        Args:
            risk_level: 风险等级
            fraud_type: 诈骗类型
            risk_score: 风险分数 (0-100)
            confidence: 置信度 (0-1)
            reasons: 判断理由列表
            advice: 建议文案
            warning_keywords: 警告关键词
            llm_analysis: 保存LLM分析数据用于调试
        """
        self.risk_level = risk_level
        self.fraud_type = fraud_type
        self.risk_score = risk_score
        self.confidence = confidence
        self.reasons = reasons or []
        self.advice = advice
        self.warning_keywords = warning_keywords or []
        self.llm_analysis = llm_analysis
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "risk_level": self.risk_level.value,
            "fraud_type": self.fraud_type,
            "risk_score": self.risk_score,
            "confidence": self.confidence,
            "reasons": self.reasons,
            "advice": self.advice,
            "warning_keywords": self.warning_keywords,
            "timestamp": self.timestamp.isoformat()
        }
    
    def to_json(self) -> Dict:
        """转换为JSON格式（用于API响应）"""
        return {
            "risk_level": self.risk_level.value,
            "fraud_type": self.fraud_type,
            "risk_score": round(self.risk_score, 2),
            "confidence": round(self.confidence, 3),
            "reasons": self.reasons,
            "advice": self.advice,
            "warning_keywords": self.warning_keywords
        }


class LLMRiskJudge:
    """LLM风险判断器"""
    
    def __init__(self, llm_analyzer: Optional[LLMAnalyzer] = None):
        """
        初始化风险判断器
        
        Args:
            llm_analyzer: LLM分析器实例，如果为None则创建新实例
        """
        self.llm_analyzer = llm_analyzer or LLMAnalyzer()
        self.preference_model = self._load_preference_model()
        logger.info("LLM风险判断器初始化完成")
    
    def _load_preference_model(self) -> Dict:
        """
        加载偏好配置模型
        可以根据不同的用户角色调整判断策略
        """
        return {
            "child": {
                "risk_threshold_high": 50,  # 儿童用户对风险的容忍度低
                "risk_threshold_medium": 25,
                "enable_guardian_notice": True,
                "emphasis_safety": True
            },
            "youth": {
                "risk_threshold_high": 60,
                "risk_threshold_medium": 30,
                "enable_guardian_notice": False,
                "emphasis_safety": False
            },
            "adult": {
                "risk_threshold_high": 70,
                "risk_threshold_medium": 40,
                "enable_guardian_notice": False,
                "emphasis_safety": False
            },
            "elderly": {
                "risk_threshold_high": 55,  # 老年用户对风险容忍度较低
                "risk_threshold_medium": 28,
                "enable_guardian_notice": True,
                "emphasis_safety": True
            },
            "high_risk": {
                "risk_threshold_high": 40,  # 高危人群对风险容忍度极低
                "risk_threshold_medium": 20,
                "enable_guardian_notice": True,
                "emphasis_safety": True
            }
        }
    
    def judge(
        self,
        user_content: str,
        similar_cases: Optional[List[Dict]] = None,
        user_role: str = "adult",
        prompt_version: PromptVersion = PromptVersion.V2_EXAMPLES,
        enable_local_fallback: bool = True
    ) -> JudgmentResult:
        """
        进行风险判断
        
        Args:
            user_content: 用户输入文本
            similar_cases: 检索到的相似案例
            user_role: 用户角色（用于调整判断标准）
            prompt_version: 使用的提示词版本
            enable_local_fallback: 当LLM失败时是否使用本地规则
        
        Returns:
            JudgmentResult对象
        """
        try:
            # 调用LLM分析
            llm_result = self.llm_analyzer.analyze_with_llm(
                user_content=user_content,
                similar_cases=similar_cases,
                prompt_version=prompt_version
            )
            
            # 基于用户角色调整结果
            adjusted_result = self._adjust_for_user_role(llm_result, user_role)
            
            # 生成最终判断结果
            judgment = self._create_judgment(
                llm_result=adjusted_result,
                user_role=user_role,
                original_llm_result=llm_result
            )
            
            return judgment
        except Exception as e:
            logger.error(f"LLM风险判断失败: {e}")
            if enable_local_fallback:
                return self.judge_with_local_rules(user_content, user_role)
            else:
                raise
    
    def _adjust_for_user_role(self, llm_result: Dict, user_role: str) -> Dict:
        """
        根据用户角色调整LLM的判断结果
        
        不同用户角色对风险的容忍度不同
        """
        preference = self.preference_model.get(user_role, self.preference_model["adult"])
        
        # 对儿童、老年人和高危人群，适度提升风险等级
        if user_role in ["child", "elderly", "high_risk"]:
            original_score = llm_result.get("risk_score", 0)
            # 增加权重
            boost_factor = 1.15 if user_role in ["child", "high_risk"] else 1.1
            adjusted_score = min(original_score * boost_factor, 100)
            llm_result["risk_score"] = adjusted_score
            
            # 重新评估风险等级
            llm_result["risk_level"] = self._score_to_level(
                adjusted_score,
                preference["risk_threshold_high"],
                preference["risk_threshold_medium"]
            )
        
        return llm_result
    
    def _score_to_level(
        self,
        risk_score: float,
        threshold_high: float = 70,
        threshold_medium: float = 40
    ) -> str:
        """根据分数转换为风险等级"""
        if risk_score >= threshold_high:
            return "高"
        elif risk_score >= threshold_medium:
            return "中"
        else:
            return "低"
    
    def _create_judgment(
        self,
        llm_result: Dict,
        user_role: str,
        original_llm_result: Dict
    ) -> JudgmentResult:
        """
        创建最终判断结果对象
        """
        risk_level = self._map_risk_level(llm_result.get("risk_level", "低"))
        fraud_type = llm_result.get("fraud_type", "无")
        risk_score = float(llm_result.get("risk_score", 0))
        confidence = float(llm_result.get("confidence", 0.5))
        
        # 获取原始原因和关键词
        reasons = llm_result.get("reasons", [])
        warning_keywords = llm_result.get("warning_keywords", [])
        
        # 生成针对用户角色的增强建议
        base_advice = llm_result.get("advice", "")
        enhanced_advice = self._enhance_advice(
            base_advice,
            risk_level,
            fraud_type,
            user_role
        )
        
        return JudgmentResult(
            risk_level=risk_level,
            fraud_type=fraud_type,
            risk_score=risk_score,
            confidence=confidence,
            reasons=reasons,
            advice=enhanced_advice,
            warning_keywords=warning_keywords,
            llm_analysis=original_llm_result
        )
    
    def _map_risk_level(self, level_str: str) -> RiskJudgmentLevel:
        """
        将字符串风险等级映射到枚举
        """
        level_str = str(level_str).lower().strip()
        if "高" in level_str or "high" in level_str:
            return RiskJudgmentLevel.HIGH
        elif "中" in level_str or "medium" in level_str:
            return RiskJudgmentLevel.MEDIUM
        else:
            return RiskJudgmentLevel.LOW
    
    def _enhance_advice(
        self,
        base_advice: str,
        risk_level: RiskJudgmentLevel,
        fraud_type: str,
        user_role: str
    ) -> str:
        """
        根据用户角色增强建议文案
        """
        role_prefixes = {
            "child": "【面向未成年人的提醒】",
            "youth": "【面向青少年的提醒】",
            "adult": "【安全提示】",
            "elderly": "【面向老年人的提醒】",
            "high_risk": "【高危人群加强防范】"
        }
        
        role_suffix = {
            "child": "请立即告诉家长或信任的成年人，不要自行处理。",
            "youth": "建议与信任的人商量后再做决定。",
            "adult": "请注意核实信息，如有疑问请联系正规部门。",
            "elderly": "请先联系子女或亲友，不要单独处理。",
            "high_risk": "您是高危人群，请立即寻求专业帮助，如有紧急情况请报警。"
        }
        
        prefix = role_prefixes.get(user_role, "【安全提示】")
        suffix = role_suffix.get(user_role, "")
        
        # 高风险时强化建议
        if risk_level == RiskJudgmentLevel.HIGH:
            if "报警" not in base_advice and user_role in ["child", "elderly", "high_risk"]:
                base_advice += " 严重情况下请立即报警或拨打96110反诈专线。"
        
        return f"{prefix}{base_advice} {suffix}".strip()
    
    def judge_with_local_rules(
        self,
        user_content: str,
        user_role: str = "adult"
    ) -> JudgmentResult:
        """
        使用本地规则进行判断（降级方案）
        """
        # 本地关键词库
        high_risk_keywords = [
            "公安局", "检察院", "法院", "安全账户", "涉嫌洗钱", "涉嫌犯罪",
            "冻结账户", "保证金", "通缉令", "逮捕令", "立即转账", "验证码"
        ]
        
        medium_risk_keywords = [
            "高回报", "投资理财", "股票", "期货", "外汇", "数字货币",
            "点击链接", "扫码", "客服", "退款", "账户异常", "需要确认"
        ]
        
        # 计算匹配数量
        content_lower = user_content.lower()
        high_matches = sum(1 for kw in high_risk_keywords if kw in content_lower)
        medium_matches = sum(1 for kw in medium_risk_keywords if kw in content_lower)
        
        # 确定风险等级和分数
        if high_matches > 0:
            risk_score = min(50 + high_matches * 15, 100)
            risk_level = RiskJudgmentLevel.HIGH if risk_score >= 70 else RiskJudgmentLevel.MEDIUM
            fraud_type = self._infer_fraud_type(user_content)
        elif medium_matches > 0:
            risk_score = min(30 + medium_matches * 10, 60)
            risk_level = RiskJudgmentLevel.MEDIUM if risk_score >= 40 else RiskJudgmentLevel.LOW
            fraud_type = "投资理财诈骗"
        else:
            risk_score = 10
            risk_level = RiskJudgmentLevel.LOW
            fraud_type = "无"
        
        # 提取匹配的关键词
        warning_keywords = [kw for kw in high_risk_keywords if kw in content_lower]
        warning_keywords.extend([kw for kw in medium_risk_keywords if kw in content_lower][:3])
        
        reasons = self._generate_local_reasons(
            risk_level,
            high_matches,
            medium_matches,
            user_content
        )
        
        advice = self._generate_local_advice(risk_level, fraud_type, user_role)
        
        return JudgmentResult(
            risk_level=risk_level,
            fraud_type=fraud_type,
            risk_score=risk_score,
            confidence=0.6,
            reasons=reasons,
            advice=advice,
            warning_keywords=warning_keywords,
            llm_analysis=None
        )
    
    def _infer_fraud_type(self, content: str) -> str:
        """根据内容推断诈骗类型"""
        fraud_keywords = {
            "冒充公检法诈骗": ["公安局", "检察院", "法院", "涉嫌", "逮捕", "通缉"],
            "投资理财诈骗": ["投资", "理财", "高回报", "股票", "期货", "基金"],
            "钓鱼诈骗": ["验证码", "密码", "扫码", "链接", "账户异常"],
            "购物退款诈骗": ["退款", "客服", "提供信息", "丰富", "售后"],
            "杀猪盘诈骗": ["交友", "感情", "转账", "困难", "投资"],
            "贷款诈骗": ["贷款", "无抵押", "放款", "审核"],
            "赌博诈骗": ["博彩", "赌场", "下注", "彩票"]
        }
        
        content_lower = content.lower()
        for fraud_type, keywords in fraud_keywords.items():
            if any(kw in content_lower for kw in keywords):
                return fraud_type
        
        return "可疑交易"
    
    def _generate_local_reasons(
        self,
        risk_level: RiskJudgmentLevel,
        high_matches: int,
        medium_matches: int,
        content: str
    ) -> List[str]:
        """生成本地规则的判断理由"""
        reasons = []
        
        if high_matches > 0:
            reasons.append(f"检测到{high_matches}个高风险关键词")
        
        if medium_matches > 0:
            reasons.append(f"检测到{medium_matches}个中风险关键词")
        
        if "转账" in content or "付款" in content:
            reasons.append("涉及资金交易")
        
        if "验证码" in content or "密码" in content:
            reasons.append("要求敏感信息")
        
        if "立即" in content or "紧急" in content:
            reasons.append("使用紧迫性语言")
        
        if not reasons:
            reasons.append("基于本地规则的风险评估")
        
        return reasons[:5]
    
    def _generate_local_advice(
        self,
        risk_level: RiskJudgmentLevel,
        fraud_type: str,
        user_role: str
    ) -> str:
        """生成本地规则的建议文案"""
        advice_map = {
            RiskJudgmentLevel.HIGH: {
                "冒充公检法诈骗": "这是典型的冒充公检法诈骗。立即停止，不要转账。正规执法部门不会通过网络要求转账，请报警处理。",
                "投资理财诈骗": "这是投资诈骗。立即停止，不要投资。不要相信'高回报'的承诺，请向有关部门举报。",
                "default": "风险极高。立即停止所有操作，不要转账或提供个人信息，请报警处理。"
            },
            RiskJudgmentLevel.MEDIUM: {
                "default": "存在诈骗风险。请勿转账或提供个人信息，核实对方身份和信息真实性。"
            },
            RiskJudgmentLevel.LOW: {
                "default": "未检测到明显诈骗迹象，但仍需保持警惕。"
            }
        }
        
        level_advice = advice_map.get(risk_level, {})
        specific_advice = level_advice.get(fraud_type) or level_advice.get("default", "")
        
        # 根据用户角色添加后缀
        if user_role == "child":
            specific_advice += " 请立即告诉家长。"
        elif user_role == "elderly":
            specific_advice += " 请先告诉家人。"
        elif user_role == "high_risk":
            specific_advice += " 您是高危人群，请提高警惕。"
        
        return specific_advice
    
    def get_judgment_report(self, judgment: JudgmentResult) -> Dict:
        """获取详细的判断报告"""
        return {
            "summary": {
                "risk_level": judgment.risk_level.value,
                "fraud_type": judgment.fraud_type,
                "risk_score": round(judgment.risk_score, 2),
                "confidence": round(judgment.confidence, 3)
            },
            "analysis": {
                "reasons": judgment.reasons,
                "warning_keywords": judgment.warning_keywords
            },
            "recommendation": {
                "advice": judgment.advice,
                "timestamp": judgment.timestamp.isoformat()
            }
        }


# 创建全局实例
llm_risk_judge = LLMRiskJudge()
