import json
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from Multimodal_processing.vector_store import collection
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import AnalysisRecord

def generate_training_data(db: Session, output_dir: str):
    """从数据库生成训练数据"""
    # 1. 获取所有标记为高风险的或用于训练的分析记录
    records = db.query(AnalysisRecord).filter(
        AnalysisRecord.risk_level == "high"
    ).limit(500).all()

    train_data = []
    for record in records:
        # 2. 构造训练样本
        text = record.input_text or "请分析这段内容是否为诈骗"
        label = record.fraud_type
        assistant_output = f"这是{label}。{record.advice}"
        train_sample = {
            "messages": [
                {"role": "user", "content": [{"text": text}]},
                {"role": "assistant", "content": [{"text": assistant_output}]}
            ]
        }
        train_data.append(train_sample)

    # 3. 写入 JSONL 文件
    output_path = os.path.join(output_dir, "train_data.jsonl")
    with open(output_path, 'w', encoding='utf-8') as f:
        for sample in train_data:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    print(f"训练数据已生成，共 {len(train_data)} 条，保存至 {output_path}")

if __name__ == "__main__":
    db = SessionLocal()
    generate_training_data(db, ".")
    db.close()