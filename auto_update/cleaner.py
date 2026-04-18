import hashlib
import re
from datetime import datetime

def clean_case(raw_data: dict) -> dict:
    """
    将原始案例数据清洗为向量库标准格式。
    raw_data 应包含 title, content, fraud_type (可选), source (可选)。
    """
    title = raw_data.get("title", "").strip()
    content = raw_data.get("content", "").strip()
    if not content:
        return None
    # 清洗文本：合并空白字符
    content = re.sub(r'\s+', ' ', content)
    text_content = f"【{title}】\n{content}" if title else content
    # 生成唯一ID（基于内容哈希）
    unique_id = hashlib.md5(text_content.encode()).hexdigest()
    fraud_type = raw_data.get("fraud_type") or "其他诈骗"
    return {
        "id": unique_id,
        "text": text_content,
        "title": title,
        "content": content,
        "type": fraud_type,
        "source": raw_data.get("source", "unknown"),
        "timestamp": datetime.now().isoformat()
    }