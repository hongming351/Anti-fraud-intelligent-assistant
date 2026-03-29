from typing import Dict, Optional
from datetime import datetime
import logging

from ..config import settings
from .. import schemas

logger = logging.getLogger(__name__)


class RiskAssessor:
    """风险评估器"""
    
    def __init__(self):
        self.risk_threshold_high = settings.RISK_THRESHOLD_HIGH
        self.risk_threshold_medium = settings.RISK_THRESHOLD_MEDIUM
        logger.info("风险评估器初始化完成")
    
    def assess_risk(self, risk_score: float) -> schemas.RiskLevel:
        """评估风险等级"""
        if risk_score >= self.risk_threshold_high:
            return schemas.RiskLevel.HIGH
        elif risk_score >= self.risk_threshold_medium:
            return schemas.RiskLevel.MEDIUM
        else:
            return schemas.RiskLevel.LOW
    
    def generate_advice(self, risk_level: schemas.RiskLevel, fraud_type: str, user_role: str) -> str:
        """生成处置建议"""
        base_advice = self._get_base_advice(risk_level, fraud_type)
        role_specific_advice = self._get_role_specific_advice(user_role, risk_level)
        
        return f"{base_advice} {role_specific_advice}"
    
    def _get_base_advice(self, risk_level: schemas.RiskLevel, fraud_type: str) -> str:
        """获取基础处置建议"""
        advice_templates = {
            schemas.RiskLevel.HIGH: {
                "impersonation": "立即中断联系！这是典型的冒充公检法诈骗，已触发监护人联动，建议立即报警或联系96110反诈专线。",
                "investment": "立即停止投资！这是高回报诈骗，资金安全受到严重威胁，建议立即报警并联系银行冻结账户。",
                "phishing": "立即停止操作！这是钓鱼诈骗，不要点击任何链接或提供验证码，建议修改相关账户密码。",
                "romance": "立即中断联系！这是杀猪盘诈骗，对方目的是骗取钱财，建议保存证据并报警。",
                "default": "立即中断联系！存在极高诈骗风险，已触发监护人联动，建议立即报警处理。"
            },
            schemas.RiskLevel.MEDIUM: {
                "shopping": "存在较大诈骗风险，请勿转账或提供个人信息，建议通过官方渠道核实客服身份。",
                "loan": "谨慎对待贷款信息，不要提前支付任何费用，建议通过正规金融机构办理贷款。",
                "gambling": "这是非法赌博诈骗，不要参与任何投注，建议举报该平台。",
                "default": "存在较大诈骗风险，请勿转账或提供个人信息，建议核实对方身份和平台真实性。"
            },
            schemas.RiskLevel.LOW: {
                "default": "无明显诈骗特征，但仍需保持警惕，避免泄露个人信息，不点击不明链接。"
            }
        }
        
        level_advice = advice_templates.get(risk_level, {})
        
        # 尝试匹配具体诈骗类型
        for key in [fraud_type, "default"]:
            if key in level_advice:
                return level_advice[key]
        
        return "请保持警惕，注意个人信息安全。"
    
    def _get_role_specific_advice(self, user_role: str, risk_level: schemas.RiskLevel) -> str:
        """获取角色特定的建议"""
        role_advice = {
            "child": {
                schemas.RiskLevel.HIGH: "已通知监护人，请立即向家长或老师报告。",
                schemas.RiskLevel.MEDIUM: "请立即告诉家长或老师，不要自行处理。",
                schemas.RiskLevel.LOW: "遇到不确定的情况要及时告诉家长。"
            },
            "youth": {
                schemas.RiskLevel.HIGH: "建议立即联系家人或朋友协助处理。",
                schemas.RiskLevel.MEDIUM: "建议与家人或朋友商量后再做决定。",
                schemas.RiskLevel.LOW: "保持警惕，多了解反诈知识。"
            },
            "elderly": {
                schemas.RiskLevel.HIGH: "已通知监护人，请不要自行操作，等待家人协助。",
                schemas.RiskLevel.MEDIUM: "请先联系子女或亲友核实情况。",
                schemas.RiskLevel.LOW: "遇到要求转账的情况一定要先联系家人。"
            },
            "high_risk": {
                schemas.RiskLevel.HIGH: "您是高危人群，已启动最高级别防护，请立即停止所有操作。",
                schemas.RiskLevel.MEDIUM: "您是高危人群，请务必通过多重验证确认对方身份。",
                schemas.RiskLevel.LOW: "您是高危人群，请保持高度警惕。"
            },
            "default": {
                schemas.RiskLevel.HIGH: "建议立即报警处理。",
                schemas.RiskLevel.MEDIUM: "建议通过官方渠道核实信息。",
                schemas.RiskLevel.LOW: "建议学习反诈知识提高防范意识。"
            }
        }
        
        role_map = {
            "child": "child",
            "youth": "youth", 
            "adult": "default",
            "elderly": "elderly",
            "high_risk": "high_risk"
        }
        
        role_key = role_map.get(user_role, "default")
        return role_advice.get(role_key, {}).get(risk_level, "")
    
    def calculate_final_risk_score(
        self, 
        base_score: float, 
        user_role: str, 
        risk_sensitivity: str,
        analysis_type: str
    ) -> float:
        """计算最终风险分数（考虑用户因素）"""
        # 角色权重
        role_weights = {
            "child": 1.3,
            "youth": 1.1,
            "adult": 1.0,
            "elderly": 1.4,
            "high_risk": 1.5
        }
        
        # 灵敏度权重
        sensitivity_weights = {
            "low": 0.8,
            "medium": 1.0,
            "high": 1.2
        }
        
        # 分析类型权重
        type_weights = {
            "text": 1.0,
            "audio": 1.1,
            "image": 1.05,
            "multimodal": 1.15
        }
        
        # 应用权重
        weighted_score = base_score
        weighted_score *= role_weights.get(user_role, 1.0)
        weighted_score *= sensitivity_weights.get(risk_sensitivity, 1.0)
        weighted_score *= type_weights.get(analysis_type, 1.0)
        
        # 限制在0-100之间
        return min(max(weighted_score, 0), 100)
    
    def should_notify_guardian(
        self, 
        risk_level: schemas.RiskLevel, 
        user_has_guardian: bool,
        risk_sensitivity: str = "medium"
    ) -> bool:
        """判断是否需要通知监护人"""
        if not user_has_guardian:
            return False
        
        # 根据风险等级和灵敏度决定
        notification_rules = {
            schemas.RiskLevel.HIGH: {
                "low": True,
                "medium": True,
                "high": True
            },
            schemas.RiskLevel.MEDIUM: {
                "low": False,
                "medium": True,
                "high": True
            },
            schemas.RiskLevel.LOW: {
                "low": False,
                "medium": False,
                "high": True
            }
        }
        
        return notification_rules.get(risk_level, {}).get(risk_sensitivity, False)
    
    def generate_analysis_result(
        self,
        risk_score: float,
        fraud_type: str,
        confidence: float,
        details: str,
        user_role: str,
        risk_sensitivity: str,
        analysis_type: str
    ) -> Dict:
        """生成完整的分析结果"""
        # 计算最终风险分数
        final_score = self.calculate_final_risk_score(
            risk_score, user_role, risk_sensitivity, analysis_type
        )
        
        # 评估风险等级
        risk_level = self.assess_risk(final_score)
        
        # 生成处置建议
        advice = self.generate_advice(risk_level, fraud_type, user_role)
        
        return {
            "risk_level": risk_level,
            "risk_score": final_score,
            "fraud_type": fraud_type,
            "confidence": confidence,
            "details": details,
            "advice": advice,
            "timestamp": datetime.now()
        }


# 创建全局风险评估器实例
risk_assessor = RiskAssessor()