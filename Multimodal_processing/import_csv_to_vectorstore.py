import os
import csv
from tqdm import tqdm
from vector_store import collection

def read_csv_with_fallback(file_path):
    """尝试用不同编码读取 CSV 文件，返回 reader 对象"""
    encodings = ['utf-8', 'gbk', 'gb18030', 'latin-1']
    for enc in encodings:
        try:
            f = open(file_path, 'r', encoding=enc)
            reader = csv.reader(f)
            # 尝试读取一行以验证编码
            next(reader)
            # 重置文件指针
            f.seek(0)
            return f, reader
        except (UnicodeDecodeError, StopIteration):
            if f:
                f.close()
            continue
    raise ValueError(f"无法用任何已知编码读取文件: {file_path}")

def import_csv_files(folder_path: str, batch_size=100):
    csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
    if not csv_files:
        print(f"在 {folder_path} 中没有找到 CSV 文件")
        return

    total_inserted = 0
    for idx, csv_file in enumerate(csv_files, 1):
        file_path = os.path.join(folder_path, csv_file)
        print(f"\n[{idx}/{len(csv_files)}] 正在处理: {csv_file}")

        prefix = os.path.splitext(csv_file)[0]
        records = []

        try:
            f, reader = read_csv_with_fallback(file_path)
        except ValueError as e:
            print(f"  错误: {e}")
            continue

        with f:
            header = next(reader)  # 跳过标题行
            for row_idx, row in enumerate(reader):
                if len(row) < 2:
                    continue
                content = row[0].strip()
                label = row[1].strip()
                if not content:
                    continue

                text_content = f"【{label}】\n{content}"
                unique_id = f"{prefix}_{row_idx}"
                records.append({
                    "id": unique_id,
                    "text": text_content,
                    "title": label,
                    "content": content,
                    "type": "telecom_fraud_case",
                    "source": "Telecom_Fraud_Texts_5"
                })

        if not records:
            print(f"  文件中没有有效数据，跳过")
            continue

        print(f"  从文件中读取到 {len(records)} 条有效案例")
        print(f"  正在分批 upsert 到向量库（每批 {batch_size} 条）...")

        total_in_file = 0
        pbar = tqdm(total=len(records), desc="  Upsert进度", unit="条")
        for start in range(0, len(records), batch_size):
            end = min(start + batch_size, len(records))
            batch = records[start:end]
            ids = [r["id"] for r in batch]
            texts = [r["text"] for r in batch]
            metadatas = [
                {
                    "title": r["title"],
                    "content": r["content"],
                    "type": r["type"],
                    "source": r["source"]
                }
                for r in batch
            ]
            collection.upsert(ids=ids, documents=texts, metadatas=metadatas)
            total_in_file += len(batch)
            pbar.update(len(batch))
        pbar.close()

        total_inserted += len(records)
        print(f"  文件 {csv_file} 处理完成，共 upsert {len(records)} 条")

    print(f"\n批量导入完成！共处理 {len(csv_files)} 个文件，新增/更新 {total_inserted} 条案例。")
    print(f"当前向量库总数据量: {collection.count()}")

if __name__ == "__main__":
    csv_folder = r"D:\Anti-fraud-intelligent-assistant\Multimodal_processing\databases\Telecom_Fraud_Texts_5-main"
    import_csv_files(csv_folder)