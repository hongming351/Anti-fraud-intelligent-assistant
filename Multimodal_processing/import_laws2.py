import os
import json
from vector_store import collection

def import_laws(json_path, id_prefix="laws2"):
    with open(json_path, 'r', encoding='utf-8') as f:
        laws = json.load(f)
    
    records = []
    for idx, law in enumerate(laws):
        title = law.get("title", "")
        content = law.get("content", "")
        if not content:
            continue
        text_content = f"【{title}】\n{content}"
        unique_id = f"{id_prefix}_{idx}"   # 使用前缀+索引确保唯一
        records.append({
            "id": unique_id,
            "text": text_content,
            "title": title,
            "content": content,
            "type": law.get("type", "unknown"),
            "source": law.get("source", "unknown")
        })
    
    if not records:
        print("没有有效数据")
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
    
    collection.upsert(ids=ids, documents=texts, metadatas=metadatas)
    print(f"成功导入/更新 {len(records)} 条法律法规")
    print(f"当前向量库总数: {collection.count()}")

if __name__ == "__main__":
    json_path = "databases/laws2.json"   # 确保路径正确
    import_laws(json_path, id_prefix="laws2")