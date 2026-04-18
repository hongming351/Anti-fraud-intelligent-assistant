import sys
import os
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from auto_update.cleaner import clean_case
from Multimodal_processing.vector_store import collection

def update_knowledge_base_job() -> dict:
    """定时任务：从反诈网站抓取新案例，清洗后存入向量库
    
    Returns:
        dict: 包含 new_count (新增案例数), details (描述信息), last_updated (ISO格式时间)
    """
    print("开始执行知识库自动更新任务...")
    
    # TODO: 调用爬虫获取最新案例
    # from app.services.crawler import fetch_latest_cases
    # raw_cases = fetch_latest_cases()
    
    # 目前先用模拟数据演示
    raw_cases = [
        {
            "title": "新型 AI 语音诈骗案例",
            "content": "骗子利用 AI 合成声音冒充子女向老人要钱...",
            "source_url": "https://example.com/case1"
        }
    ]
    
    new_count = 0
    for case in raw_cases:
        # 适配 clean_case 需要的格式
        standardized = {
            "title": case["title"],
            "content": case["content"],
            "fraud_type": "其他诈骗",
            "source": case.get("source_url", "web_crawler")
        }
        cleaned = clean_case(standardized)
        if cleaned:
            # 使用 upsert 避免重复
            collection.upsert(
                ids=[cleaned["id"]],
                documents=[cleaned["text"]],
                metadatas=[{k: v for k, v in cleaned.items() if k != 'text'}]
            )
            new_count += 1
    
    # 记录最后更新时间（无论是否新增，只要任务执行就记录）
    last_updated = datetime.now()
    last_update_file = os.path.join(os.path.dirname(__file__), "last_update.txt")
    with open(last_update_file, "w") as f:
        f.write(last_updated.isoformat())
    
    print(f"自动更新完成，新增/更新 {new_count} 条案例，当前向量库总数: {collection.count()}, 更新时间: {last_updated}")
    
    return {
        "new_count": new_count,
        "details": f"本次更新新增/更新 {new_count} 条案例，当前向量库总数: {collection.count()}",
        "last_updated": last_updated.isoformat()
    }