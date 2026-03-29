import re
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TextAnalyzer:
    """文本分析器"""
    
    def __init__(self):
        # 初始化关键词库
        self.keyword_patterns = self._load_keyword_patterns()
        logger.info("文本分析器初始化完成")
    
    def _load_keyword_patterns(self) -> Dict[str, List[str]]:
        """加载关键词模式"""
        return {
            "impersonation": [
                "公安局", "检察院", "法院", "安全账户", "涉嫌洗钱", "冻结账户", 
                "保证金", "通缉令", "逮捕令", "刑事拘留", "传票"
            ],
            "investment": [
                "高回报", "稳赚不赔", "内幕消息", "数字货币", "区块链", 
                "投资理财", "股票推荐", "期货", "外汇", "私募"
            ],
            "phishing": [
                "验证码", "点击链接", "扫码", "登录", "密码", "账号异常",
                "系统升级", "安全认证", "身份验证", "重置密码"
            ],
            "shopping": [
                "客服", "退款", "退货", "快递", "包裹", "中奖", "免费",
                "优惠券", "打折", "限时抢购", "秒杀"
            ],
            "romance": [
                "交友", "恋爱", "见面", "转账", "困难", "急需用钱",
                "生病", "住院", "手术", "车祸", "家庭变故"
            ],
            "loan": [
                "贷款", "无抵押", "低利息", "快速放款", "信用贷", "网贷",
                "套现", "提额", "信用卡", "白条"
            ],
            "gambling": [
                "博彩", "赌场", "彩票", "下注", "赔率", "庄家",
                "棋牌", "老虎机", "百家乐", "轮盘"
            ]
        }
    
    def analyze_text(self, text: str, enable_deep_analysis: bool = True) -> Dict:
        """分析文本内容"""
        if not text or not text.strip():
            return {
                "risk_score": 0,
                "fraud_type": "正常交流",
                "confidence": 0.0,
                "details": "文本内容为空",
                "keywords_found": []
            }
        
        # 基础关键词匹配
        keyword_matches = self._match_keywords(text)
        
        # 计算风险分数
        risk_score = self._calculate_risk_score(keyword_matches)
        
        # 确定诈骗类型
        fraud_type = self._determine_fraud_type(keyword_matches)
        
        # 计算置信度
        confidence = self._calculate_confidence(risk_score, len(keyword_matches))
        
        # 生成详细分析
        details = self._generate_details(keyword_matches, text)
        
        # 如果需要深度分析
        if enable_deep_analysis:
            deep_analysis = self._deep_analysis(text)
            risk_score = (risk_score + deep_analysis["risk_score"]) / 2
            confidence = max(confidence, deep_analysis["confidence"])
            details += f" | {deep_analysis['details']}"
        
        # 限制风险分数在0-100之间
        risk_score = min(max(risk_score, 0), 100)
        
        return {
            "risk_score": risk_score,
            "fraud_type": fraud_type,
            "confidence": confidence,
            "details": details,
            "keywords_found": keyword_matches
        }
    
    def _match_keywords(self, text: str) -> List[Dict]:
        """匹配关键词"""
        matches = []
        text_lower = text.lower()
        
        for pattern_type, keywords in self.keyword_patterns.items():
            for keyword in keywords:
                if keyword in text_lower:
                    matches.append({
                        "type": pattern_type,
                        "keyword": keyword,
                        "weight": self._get_keyword_weight(pattern_type)
                    })
        
        return matches
    
    def _get_keyword_weight(self, pattern_type: str) -> float:
        """获取关键词权重"""
        weights = {
            "impersonation": 1.5,
            "investment": 1.3,
            "phishing": 1.2,
            "shopping": 1.1,
            "romance": 1.4,
            "loan": 1.2,
            "gambling": 1.3
        }
        return weights.get(pattern_type, 1.0)
    
    def _calculate_risk_score(self, matches: List[Dict]) -> float:
        """计算风险分数"""
        if not matches:
            return 0
        
        base_score = 0
        for match in matches:
            base_score += 10 * match["weight"]
        
        # 考虑匹配数量
        match_count_factor = min(len(matches) * 5, 30)
        
        return min(base_score + match_count_factor, 100)
    
    def _determine_fraud_type(self, matches: List[Dict]) -> str:
        """确定诈骗类型"""
        if not matches:
            return "正常交流"
        
        # 统计每种类型的匹配数量
        type_counts = {}
        for match in matches:
            pattern_type = match["type"]
            type_counts[pattern_type] = type_counts.get(pattern_type, 0) + 1
        
        # 找到匹配数量最多的类型
        if type_counts:
            main_type = max(type_counts.items(), key=lambda x: x[1])[0]
            type_names = {
                "impersonation": "冒充公检法诈骗",
                "investment": "投资理财诈骗",
                "phishing": "钓鱼诈骗",
                "shopping": "购物退款诈骗",
                "romance": "杀猪盘诈骗",
                "loan": "贷款诈骗",
                "gambling": "赌博诈骗"
            }
            return type_names.get(main_type, "可疑诈骗")
        
        return "可疑诈骗"
    
    def _calculate_confidence(self, risk_score: float, match_count: int) -> float:
        """计算置信度"""
        if risk_score == 0:
            return 0.0
        
        # 基础置信度基于风险分数
        base_confidence = min(risk_score / 100, 0.9)
        
        # 匹配数量增加置信度
        match_confidence = min(match_count * 0.1, 0.3)
        
        return min(base_confidence + match_confidence, 0.98)
    
    def _generate_details(self, matches: List[Dict], original_text: str) -> str:
        """生成详细分析"""
        if not matches:
            return "未检测到可疑关键词"
        
        # 统计信息
        match_count = len(matches)
        types_found = set(match["type"] for match in matches)
        
        # 构建详情
        details = f"检测到{match_count}个可疑关键词，涉及{len(types_found)}种诈骗类型。"
        
        # 添加具体关键词
        if match_count <= 5:
            keywords = [match["keyword"] for match in matches[:5]]
            details += f" 关键词: {', '.join(keywords)}"
        
        # 检查紧急关键词
        urgent_keywords = ["安全账户", "涉嫌洗钱", "转账", "验证码"]
        for keyword in urgent_keywords:
            if keyword in original_text.lower():
                details += " 包含紧急风险关键词！"
                break
        
        return details
    
    def _deep_analysis(self, text: str) -> Dict:
        """深度分析（模拟）"""
        # 这里可以集成更复杂的NLP模型
        # 目前使用简单的模式匹配
        
        # 检查URL
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)
        
        # 检查电话号码
        phone_pattern = r'1[3-9]\d{9}'
        phones = re.findall(phone_pattern, text)
        
        # 检查金额
        amount_pattern = r'(\d+[万千]?元|\d+[\.\d]*万|\d+[\.\d]*千)'
        amounts = re.findall(amount_pattern, text)
        
        risk_score = 0
        details_parts = []
        
        if urls:
            risk_score += 15
            details_parts.append(f"包含{len(urls)}个链接")
        
        if phones:
            risk_score += 10
            details_parts.append(f"包含{len(phones)}个电话号码")
        
        if amounts:
            risk_score += 20
            details_parts.append(f"提及金额: {', '.join(amounts[:3])}")
        
        # 检查紧急语气
        urgent_words = ["立即", "马上", "赶紧", "快", "紧急", "立刻"]
        urgent_count = sum(1 for word in urgent_words if word in text)
        if urgent_count > 0:
            risk_score += urgent_count * 5
            details_parts.append("使用紧急语气")
        
        details = "深度分析: " + " | ".join(details_parts) if details_parts else "深度分析未发现异常"
        
        return {
            "risk_score": risk_score,
            "confidence": min(0.3 + risk_score / 100 * 0.5, 0.8),
            "details": details
        }
    
    def update_keywords(self, pattern_type: str, keywords: List[str]):
        """更新关键词库"""
        if pattern_type in self.keyword_patterns:
            self.keyword_patterns[pattern_type].extend(keywords)
            # 去重
            self.keyword_patterns[pattern_type] = list(set(self.keyword_patterns[pattern_type]))
            logger.info(f"更新{pattern_type}类型关键词，当前数量: {len(self.keyword_patterns[pattern_type])}")
        else:
            self.keyword_patterns[pattern_type] = keywords
            logger.info(f"新增{pattern_type}类型关键词")


# 创建全局分析器实例
text_analyzer = TextAnalyzer()