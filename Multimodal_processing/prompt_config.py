"""
反诈智能助手 - Prompt 配置与风险阈值管理
===============================================
功能：
1. 统一管理大模型提示词（Prompt）
2. 定义针对不同人群的风险阈值
3. 提供风险等级评估标准

作者：反诈AI团队
版本：2.0
更新时间：2024-11
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict


# ========== 人群类型定义 ==========
class UserDemographic(Enum):
    """用户人群分类"""
    ELDERLY = "elderly"          # 老年人（60岁以上）
    CHILDREN = "children"        # 儿童（18岁以下）
    ADULT = "adult"              # 青壮年成年人（18-60岁）


# ========== 风险阈值配置 ==========
@dataclass
class RiskThresholds:
    """
    针对不同人群的精细化风险阈值配置
    
    关键概念：
    - risk_level: 分为 high (高], medium (中), low (低), safe (安全)
    - confidence_threshold: 模型输出的置信度超过此阈值才算作相应风险等级
    - trigger_threshold: 触发该风险等级的最低置信度
    """
    
    # 概览文档中的阈值定义
    high_threshold: float      # high 等级的阈值
    medium_threshold: float    # medium 等级的阈值  
    low_threshold: float       # low 等级的阈值
    
    # 人群特异化调整
    demographic: str           # 对应的人群类型
    description: str           # 阈值调整说明


# ========== 针对不同人群的风险阈值 - 详细说明 ==========

RISK_THRESHOLDS_CONFIG = {
    UserDemographic.ELDERLY: RiskThresholds(
        high_threshold=0.65,
        medium_threshold=0.45,
        low_threshold=0.25,
        demographic="elderly",
        description="""
【老年人风险阈值】- 更严格的保护策略
理由分析：
1. 信息辨别能力下降：认知和信息处理速度随年龄增加而下降
2. 被骗风险率高：统计数据显示60岁以上被骗人群占总数的30-40%
3. 投资理财诈骗易感：退休储蓄充足但缺乏投资知识，容易信任强势推销
4. 保健品诈骗高发：对健康问题焦虑，虚假医疗宣传极易触发情感按钮
5. 社交孤立感：子女不在身边，容易从"关心者"的诈骗中掉入陷阱（杀猪盘）

阈值调整方案：
- HIGH: 0.65（降低5%）- 只要有明确诈骗信号即触发，不过度依赖AI置信度
- MEDIUM: 0.45（降低10%）- 可疑信息更容易被标记为中危
- LOW: 0.25（降低5%）- 轻微异常也会被记录在案

触发加强措施：
✓ 包含"投资"、"保本"、"收益"等金融词汇 → 自动升级为HIGH
✓ 包含"医疗"、"健康"、"特效"等医疗词汇 → 自动升级为HIGH
✓ 涉及汇款、转账、支付 → 直接标记为HIGH，拒绝操作
✓ 包含感情诱导话术 → 自动升级为MEDIUM及以上
"""
    ),
    
    UserDemographic.CHILDREN: RiskThresholds(
        high_threshold=0.70,
        medium_threshold=0.50,
        low_threshold=0.30,
        demographic="children",
        description="""
【儿童/青少年风险阈值】- 娱乐类诈骗防护
理由分析：
1. 游戏充值诈骗高发：儿童/青少年是游戏玩家主体，充值诈骗最常见
2. 虚拟资产交易易上当：对真实金钱价值认知不足，容易被虚假承诺欺骗
3. 社交媒体风险：在抖音、快手等平台被主播诱导打赏、参与"抽奖"
4. 追星诈骗易感群体：粉丝文化中容易被利用，虚假应援、投票诈骗频繁
5. 信息甄别能力弱：难以分辨真假网站、假冒账号

阈值调整方案：
- HIGH: 0.70（保持正常）- 防止过度告警
- MEDIUM: 0.50（降低10%）- 降低虚拟资产交易的触发阈值
- LOW: 0.30（降低10%）- 轻微异常即预警

风险词库加强：
✓ "游戏充值"、"装备交易"、"账号出售" → 自动升级为HIGH
✓ "抽奖"、"免费领取"、"先充值后返利" → 自动升级为HIGH
✓ "应援"、"刷礼物"、"粉丝福利" → 自动升级为MEDIUM及以上
✓ 链接、二维码、支付任何内容 → 建议家长审核，记录为HIGH

家长跟踪建议：
⚠️ 建议系统向家长推送实时告警
⚠️ 高危交易自动锁定，需要家长验证
"""
    ),
    
    UserDemographic.ADULT: RiskThresholds(
        high_threshold=0.75,
        medium_threshold=0.55,
        low_threshold=0.35,
        demographic="adult",
        description="""
【青壮年成年人风险阈值】- 平衡的防护策略
理由分析：
1. 信息处理能力强：成年人一般具备较强的逻辑思维和批判性思维
2. 工作诈骗高发：刷单诈骗、虚假兼职主要瞄准这个群体的经济需求
3. 投资理财风险：相对老年人，投资风险承受度高，但仍需防范高收益诈骗
4. 交友与感情诈骗：成年人是杀猪盘、交友诈骗的主要受害群体
5. 平衡安全与便利：过度告警会降低用户体验

阈值调整方案（标准方案）：
- HIGH: 0.75（正常基准）- 明确诈骗信号才触发
- MEDIUM: 0.55（正常基准）- 可疑信息触发
- LOW: 0.35（正常基准）- 轻微异常触发

风险词库标准：
✓ "立即转账"、"扫码支付"、"二维码" → HIGH
✓ "年化20%+"、"保本保收益" → HIGH
✓ "日赚300+"、"垫付秒返" → HIGH
✓ 陌生人加好友、不明来源链接 → MEDIUM
✓ 业务逻辑不清、中文错别字 → LOW

用户建议：
✅ 标准防骗提示即可
✅ 鼓励用户进行必要的身份验证
"""
    ),
}


# ========== 风险等级定义与判断标准 ==========

FRAUD_SYSTEM_PROMPT = """## 角色身份
你是一名资深的反诈专家，拥有15年网络诈骗案件分析经验。你将承担AI诈骗风险识别员的职责。

## 核心任务
1. 精准识别内容中的诈骗风险信号
2. 准确分类诈骗类型（覆盖10种以上主流诈骗手法）
3. 提供可操作的防骗建议
4. 输出结构化JSON评估报告

## 诈骗类型库（按高发排序）
1. 刷单诈骗：承诺高佣金诱导垫付，常见话术"日赚300+"、"垫付秒返"
2. 冒充公检法：谎称违法犯罪，诱导转账到"安全账户"
3. 杀猪盘/交友诈骗：虚构身份骗取感情和资金
4. 虚假投资理财：承诺高额回报（年化20%+）引诱投资
5. 冒充客服退款：设置退款陷阱或诱导点击钓鱼链接
6. 虚假贷款："秒批"、"无需征信"来诱导提交个人信息
7. 游戏交易诈骗：账号/装备交易后失联或要求补价
8. 追星诈骗：以投资明星企划为名诱导转账
9. 养生保健品诈骗：虚假医疗宣传+神奇疗效吸引老年人
10. AI换脸/深度伪造诈骗：利用合成视频/语音进行冒充

## 风险等级定义与判断标准

### HIGH（高危）[置信度 > 0.75]
明确的转账指令、诱导支付、投资承诺或已实施欺骗行为
示例信号：
- 二维码、银行卡号、支付链接
- "立即转账"、"先垫付"、"扫码支付"
- "年化20%+"、"保本保收益"
- 虚假身份 + 资金诱导的组合

判断原则：优先识别"明确的转账诱导"和"虚假身份+资金诱导"为高危

### MEDIUM（中危）[置信度 0.50-0.75]
存在可疑但不直接要求金钱的诱导
示例信号：
- 不明来源链接
- 陌生人加好友、不明身份
- 隐晦的身份冒充
- 业务逻辑不清但可能有恶意

判断原则：宣传不实或诱导行为，但诱导方式不直接

### LOW（低危）[置信度 0.25-0.50]
轻微异常但合理怀疑空间大
示例信号：
- 不寻常的问候
- 中文错别字
- 业务逻辑不一致但非明确诈骗
- 可能是业务员作风不专业

判断原则：轻微异常但无明确恶意，保守倾向

### SAFE（安全）[置信度 < 0.25]
完全正常的社交/商业交互
示例：
- 正常招聘信息
- 合法的商业推介
- 正常的日常沟通

## 少样本学习示例 - 增强理解

### 示例1：刷单诈骗（高危）
【输入】文本：您好，我们招网络兼职，日赚300+，需要先垫付29.9元购买产品，完成任务后立即返还佣金。请扫码支付。
【输出】{
  "risk_level": "high",
  "fraud_type": "刷单诈骗",
  "confidence": 0.98,
  "suspicious_keywords": ["日赚300+", "垫付", "扫码支付"],
  "reason": "典型刷单诈骗话术：(1)虚假高佣金诱导；(2)明确要求前期垫付；(3)提供收款二维码。受害者垫付后通常无法收到返利。",
  "advice": "⚠️【高危预警】这是常见的诈骗套路！真正的兼职不会要求先垫付。请立即停止联系，不要转账。"
}

### 示例2：冒充公检法（高危）
【输入】文本：您好，我是人民法院法官，您的账户涉嫌洗钱，需要立即冻结。请将资金转入司法监管账户以证明清白。
【输出】{
  "risk_level": "high",
  "fraud_type": "冒充公检法",
  "confidence": 0.99,
  "suspicious_keywords": ["人民法院", "涉嫌洗钱", "转账到安全账户"],
  "reason": "典型冒充公检法诈骗：(1)冒充司法机构；(2)虚构违法事实制造恐慌；(3)要求转账到指定账户。",
  "advice": "🚨【紧急】公检法从不通过电话/短信处理案件也不会要求转账。这100%是诈骗。请挂断并报警。"
}

### 示例3：虚假投资理财（中危）
【输入】文本：股票投资机会，我的客户年化收益22%，保本保收益。感兴趣可加微信详谈。
【输出】{
  "risk_level": "medium",
  "fraud_type": "虚假投资理财诈骗",
  "confidence": 0.85,
  "suspicious_keywords": ["年化22%", "保本保收益", "加微信"],
  "reason": "存在投资诈骗特征：(1)承诺高于市场正常收益的回报；(2)声称保本保收益（违反投资常识）；(3)通过隐蔽渠道拉人。",
  "advice": "⚠️【警惕】天下没有'保本+高收益'的投资。这通常是前期返利后期卷款的套路。建议查证资质。"
}

### 示例4：游戏装备交易（中危-儿童人群升级为高危）
【输入】文本：7级号便宜转，已实名，先给你截图看资料，收款后3秒内交账号。加微信：XXXXX
【输出】{
  "risk_level": "medium",
  "fraud_type": "游戏交易诈骗",
  "confidence": 0.80,
  "suspicious_keywords": ["账号交易", "先看截图", "收款后交"],
  "reason": "虽然表面看有一定逻辑，但风险特征明显：(1)账号交易易产生纠纷；(2)声称'收款后即交'，但难以追溯；(3)多数骗子最终失联或索要补价。",
  "advice": "⚠️【风险提示】游戏账号交易存在很大风险。建议通过官方交易平台，切勿直接转账给陌生人。【儿童注意】请告知家长！"
}

### 示例5：正常商业信息（安全）
【输入】文本：我们公司正在招聘产品经理，要求5年工作经验，月薪15k-20k。有意请投递简历到HR@company.com
【输出】{
  "risk_level": "safe",
  "fraud_type": "无诈骗",
  "confidence": 0.99,
  "suspicious_keywords": [],
  "reason": "正常招聘信息特征：(1)明确的岗位要求；(2)合理的薪资范围；(3)正式企业邮箱；(4)无诱导转账等异常。",
  "advice": "✅【安全】这是正常的招聘信息，建议按标准流程投递。"
}

## 输出格式要求
必须返回JSON格式，包含以下字段：
{
  "risk_level": "high|medium|low|safe",          // 风险等级
  "fraud_type": "具体诈骗类型或无诈骗",          // 从上述类型库选择
  "confidence": 0.75-0.99,                       // 判断置信度(0-1)
  "suspicious_keywords": ["关键词1", "关键词2"], // 引发怀疑的关键词列表
  "reason": "详细判断依据（50-200字）",         // 为什么得出这个结论
  "advice": "针对用户的防骗建议（包含emoji）"   // 可操作的建议文案
}

## 判断原则（优先级排序）
1. 优先识别"明确的转账诱导"为高危 ✓✓✓
2. 虚假身份 + 资金诱导 = 高危 ✓✓✓
3. 宣传不实或诱导行为 = 中危 ✓✓
4. 轻微异常但无明确恶意 = 低危 ✓
5. 无异常信号 = 安全 ✓

## 注意事项
- 避免过度诠释，严格按信息内容判断
- 对不明确的情况倾向于保守判断（偏向风险上升）
- 所有输出必须是有效的JSON格式
- 中文输出，使用简体字
"""


# ========== 风险阈值应用函数 ==========

def get_risk_thresholds(demographic: UserDemographic) -> RiskThresholds:
    """
    获取特定人群的风险阈值
    
    Args:
        demographic: 用户人群类型
        
    Returns:
        RiskThresholds 对象
    """
    return RISK_THRESHOLDS_CONFIG.get(demographic, RISK_THRESHOLDS_CONFIG[UserDemographic.ADULT])


def adjust_confidence_by_demographic(
    original_confidence: float,
    risk_level: str,
    demographic: UserDemographic
) -> tuple[str, float]:
    """
    根据人群类型调整置信度并重新评级
    
    Args:
        original_confidence: 原始置信度（来自LLM）
        risk_level: 原始风险等级
        demographic: 用户人群类型
        
    Returns:
        (调整后的风险等级, 调整后的置信度)
    """
    thresholds = get_risk_thresholds(demographic)
    
    # 根据新的阈值重新评级
    if original_confidence >= thresholds.high_threshold:
        return ("high", original_confidence)
    elif original_confidence >= thresholds.medium_threshold:
        return ("medium", original_confidence)
    elif original_confidence >= thresholds.low_threshold:
        return ("low", original_confidence)
    else:
        return ("safe", original_confidence)


def should_escalate_for_demographic(
    fraud_type: str,
    demographic: UserDemographic,
    keywords: list
) -> bool:
    """
    根据人群类型和诈骗特征，判断是否应该升级风险等级
    
    Args:
        fraud_type: 诈骗类型
        demographic: 用户人群类型
        keywords: 可疑关键词列表
        
    Returns:
        True 表示应该升级到 HIGH
    """
    
    # 老年人特异化升级规则
    if demographic == UserDemographic.ELDERLY:
        elderly_keywords = ["投资", "保本", "收益", "医疗", "健康", "特效", "保健", "养生"]
        if any(kw in keywords for kw in elderly_keywords):
            return True
        if fraud_type in ["虚假投资理财诈骗", "养生保健品诈骗"]:
            return True
    
    # 儿童特异化升级规则
    if demographic == UserDemographic.CHILDREN:
        children_keywords = ["游戏", "充值", "装备", "账号", "抽奖", "应援", "粉丝", "主播", "礼物"]
        if any(kw in keywords for kw in children_keywords):
            return True
        if fraud_type in ["游戏交易诈骗", "追星诈骗"]:
            return True
    
    return False


# ========== Prompt 获取函数 ==========

def get_fraud_system_prompt() -> str:
    """
    获取反诈系统提示词（包含角色定义、少样本学习等）
    供 multimodal_processor 调用
    
    Returns:
        str: 完整的反诈系统提示词
    """
    return FRAUD_SYSTEM_PROMPT


def get_text_analysis_user_prompt(text: str) -> str:
    """
    生成文本分析的用户提示词
    
    Args:
        text: 待分析的文本内容
        
    Returns:
        str: 用户提示词
    """
    return f"""请分析以下文本内容是否存在诈骗风险，严格按照JSON格式输出完整评估报告。

【待分析文本】
{text}

【分析要点】
1. 是否包含诱导转账、支付、投资等金钱相关的请求
2. 是否存在虚假身份冒充或权威欺骗
3. 是否包含高额回报承诺、虚假救援等社交工程话术
4. 综合判断风险等级并给出明确建议"""


def get_image_analysis_user_prompt() -> str:
    """
    生成图片分析的用户提示词
    
    Returns:
        str: 用户提示词
    """
    return """请分析这张图片中的诈骗风险，严格按照JSON格式输出结果。重点关注：
1. 是否有二维码、转账二维码、收款码
2. 是否包含"立即转账"、"扫码支付"、"垫付"等明确支付指令
3. 是否宣传"高收益"、"保本保收益"、"日赚"等虚假承诺
4. 是否存在虚假身份冒充（如冒充官方、警方、客服等）
5. 提取所有可见文字并识别诈骗关键词"""

