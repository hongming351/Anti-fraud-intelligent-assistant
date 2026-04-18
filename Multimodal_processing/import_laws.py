import os
import json
from vector_store import collection  # 导入你已有的collection对象

def load_laws(json_path: str):
    with open(json_path, 'r', encoding='utf-8') as f:
        laws = json.load(f)
    
    records = []
    for idx, law in enumerate(laws):
        title = law.get("title", "")
        content = law.get("content", "")
        # 将标题和内容拼接成适合检索的文本格式
        text_content = f"【{title}】\n{content}"
        # 生成一个唯一ID，这里简单使用 "law_" 加序号
        unique_id = f"law_{idx}"
        records.append({
            "id": unique_id,
            "text": text_content,
            "title": title,
            "content": content,
            "type": law.get("type", "law"),
            "source": law.get("source", "unknown")
        })
    return records

def insert_laws(records):
    if not records:
        return
    ids = [r["id"] for r in records]
    texts = [r["text"] for r in records]
    metadatas = [
        {
            "title": r["title"],
            "content": r["content"],
            "type": r["type"],
            "source": r["source"]
        }
        for r in records
    ]
    # 使用 upsert 可以避免重复插入，如果ID已存在则更新
    collection.upsert(ids=ids, documents=texts, metadatas=metadatas)
    print(f"成功插入/更新 {len(records)} 条法律法规")

if __name__ == "__main__":
    # 请确保 laws.json 文件在当前目录下，或者修改为你的文件路径
    json_path = r"D:\Anti-fraud-intelligent-assistant\Multimodal_processing\databases\laws.json" 
    if os.path.exists(json_path):
        laws_records = load_laws(json_path)
        insert_laws(laws_records)
        print(f"向量库当前总数: {collection.count()}")
    else:
        print(f"文件 {json_path} 不存在，请检查路径")