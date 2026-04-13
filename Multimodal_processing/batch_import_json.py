import os
import json
import glob
import time
from vector_store import collection  # 复用已有的 collection

def load_baidu_fraud_data(json_path: str, file_basename: str) -> list:
    """从百度反诈格式的 JSON 文件中提取数据"""
    print(f"  正在读取文件: {json_path}")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    records = []
    source_data = data.get("source_data", [])
    print(f"  文件中包含 {len(source_data)} 条原始记录")
    for idx, item in enumerate(source_data):
        title = item.get("title", "")
        content = item.get("content", "")
        if not title or not content:
            continue
        text_content = f"【{title}】\n{content}"
        unique_id = f"{file_basename}_{idx}"
        records.append({
            "id": unique_id,
            "text": text_content,
            "title": title,
            "content": content,
            "type": "fraud_case",
            "source": "百度反诈"
        })
    print(f"  成功提取 {len(records)} 条有效案例")
    return records

def insert_records_to_chroma(records: list, collection):
    """使用 upsert 插入或更新记录"""
    if not records:
        print("  没有记录需要插入，跳过")
        return
    print(f"  开始插入 {len(records)} 条记录到向量库...")
    start_time = time.time()
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
    elapsed = time.time() - start_time
    print(f"  已 upsert {len(records)} 条记录，耗时 {elapsed:.2f} 秒")

def batch_import_folder(folder_path: str):
    json_files = glob.glob(os.path.join(folder_path, "*.json"))
    if not json_files:
        print(f"在 {folder_path} 中没有找到 JSON 文件")
        return
    print(f"找到 {len(json_files)} 个 JSON 文件")
    total = 0
    for idx, json_file in enumerate(json_files, 1):
        print(f"\n[{idx}/{len(json_files)}] 处理: {os.path.basename(json_file)}")
        file_basename = os.path.splitext(os.path.basename(json_file))[0]
        records = load_baidu_fraud_data(json_file, file_basename)
        if records:
            insert_records_to_chroma(records, collection)
            total += len(records)
        else:
            print(f"  未提取到数据，跳过")
    print(f"\n批量导入完成！共处理 {len(json_files)} 个文件，新增/更新 {total} 条案例。")
    print(f"当前向量库总数据量: {collection.count()}")

if __name__ == "__main__":
    json_folder = r"D:\Anti-fraud-intelligent-assistant\Multimodal_processing\databases\反诈数据集"
    batch_import_folder(json_folder)