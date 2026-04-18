import os
import json
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict

# ================== 1. 初始化 ChromaDB ==================
# 指定本地持久化目录
DB_PATH = os.path.join(os.path.dirname(__file__), "vector_database")
os.makedirs(DB_PATH, exist_ok=True)

# 创建 ChromaDB 客户端（持久化模式）
client = chromadb.PersistentClient(path=DB_PATH)
print(f"ChromaDB 向量数据库已初始化，数据目录: {DB_PATH}")

# ================== 2. 配置 Embedding 模型 ==================
# 使用 sentence-transformers 模型将文本转为向量
# 设置国内镜像加速（解决 huggingface 连接问题）
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

# 加载轻量级中文 Embedding 模型（首次运行会自动下载约 400MB）
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name='paraphrase-multilingual-MiniLM-L12-v2',  # 支持中文的模型
    device='cpu'  # 使用 CPU，如你有 GPU 可改为 'cuda'
)

print(f"Embedding 模型加载完成，模型名称: paraphrase-multilingual-MiniLM-L12-v2")

# ================== 3. 创建或获取 Collection（不再删除已有数据） ==================
COLLECTION_NAME = "fraud_knowledge_base"

# 使用 get_or_create_collection 避免每次清空数据
collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=embedding_fn,
    metadata={"hnsw:space": "cosine"}  # 使用余弦相似度
)

print(f"Collection '{COLLECTION_NAME}' 已就绪，当前数据量: {collection.count()}")

# ================== 4. 准备反诈数据（示例，仅用于首次填充） ==================
def load_fraud_data_from_json(json_path: str) -> List[Dict]:
    """从百度反诈 JSON 文件中提取数据"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    records = []
    for idx, item in enumerate(data.get("source_data", [])):
        # 将标题和内容拼接成待检索的文本
        text_content = f"【{item['title']}】\n{item['content']}"
        
        records.append({
            "id": f"baidu_{idx}",  # 生成唯一ID
            "text": text_content,
            "title": item['title'],
            "content": item['content'],
            "type": "baidu_fraud_case",  # 标记数据来源
            "source": "百度反诈课堂"
        })
    return records

# 加载你的数据（请修改为实际路径）
json_path = os.path.join(os.path.dirname(__file__), "databases", "Telecom_Fraud_Texts_5-main", "百度反诈(1).json")
if os.path.exists(json_path):
    fraud_records = load_fraud_data_from_json(json_path)
    print(f"加载了 {len(fraud_records)} 条反诈案例")
else:
    # print(f"文件 {json_path} 不存在，请检查路径")
    fraud_records = []

# ================== 5. 添加手动录入的反诈法律法规 ==================
laws = [
    "《反电信网络诈骗法》规定：任何单位和个人不得非法买卖、出租、出借电话卡、物联网卡、电信线路、短信端口、银行账户、支付账户、互联网账号等。",
    "《刑法》第266条：诈骗公私财物，数额较大的，处三年以下有期徒刑、拘役或者管制，并处或者单处罚金；数额巨大或者有其他严重情节的，处三年以上十年以下有期徒刑，并处罚金。",
    "公安部提醒：公检法机关不会通过电话办案，不会要求转账到'安全账户'。"
]

for idx, law in enumerate(laws):
    fraud_records.append({
        "id": f"law_{idx}",
        "text": law,
        "title": law[:30] + "...",
        "content": law,
        "type": "law_regulation",
        "source": "法律法规"
    })

# ================== 6. 插入数据到 ChromaDB（仅当 collection 为空时插入，避免重复） ==================
def insert_records_to_chroma(records: List[Dict]):
    """将记录插入 ChromaDB（仅当记录不存在时）"""
    if not records:
        print("没有数据可插入")
        return
    
    # 检查哪些 ID 已存在
    existing_ids = set()
    for record in records:
        try:
            existing = collection.get(ids=[record["id"]])
            if existing['ids']:
                existing_ids.add(record["id"])
        except:
            pass
    
    new_records = [r for r in records if r["id"] not in existing_ids]
    if not new_records:
        print("所有数据已存在，无需插入")
        return
    
    # 提取数据
    ids = [r["id"] for r in new_records]
    texts = [r["text"] for r in new_records]
    metadatas = [
        {
            "title": r.get("title", ""),
            "content": r.get("content", ""),
            "type": r.get("type", ""),
            "source": r.get("source", "")
        }
        for r in new_records
    ]
    
    # 批量插入（ChromaDB 会自动向量化）
    print(f"正在插入 {len(texts)} 条新数据到 ChromaDB...")
    collection.add(
        ids=ids,
        documents=texts,
        metadatas=metadatas
    )
    
    print(f"成功插入 {len(new_records)} 条数据到向量库")

# 仅在当前脚本直接运行时执行插入，避免作为模块导入时重复插入
if __name__ == "__main__":
    insert_records_to_chroma(fraud_records)
    print(f"向量库中共有 {collection.count()} 条数据")

# ================== 7. 检索相似案例（供外部调用） ==================
def search_similar_cases(query_text: str, top_k: int = 3) -> List[Dict]:
    """
    根据查询文本检索最相似的反诈案例
    
    Args:
        query_text: 用户输入的文本（或从图片/音频中提取的文字）
        top_k: 返回最相似的 K 条结果
    
    Returns:
        相似案例列表，每条包含 text, type, distance 等信息
    """
    # 执行向量检索（ChromaDB 会自动将查询文本向量化）
    results = collection.query(
        query_texts=[query_text],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )
    
    # 整理返回结果
    similar_cases = []
    if results['documents'] and results['documents'][0]:
        for i in range(len(results['documents'][0])):
            similar_cases.append({
                "text": results['documents'][0][i],
                "type": results['metadatas'][0][i].get("type", ""),
                "source": results['metadatas'][0][i].get("source", ""),
                "title": results['metadatas'][0][i].get("title", ""),
                "similarity_score": 1 - results['distances'][0][i],  # ChromaDB 返回的是距离，转换为相似度
                "id": results['ids'][0][i] if results['ids'] else None
            })
    
    return similar_cases

# 明确导出的公共接口
__all__ = ['collection', 'search_similar_cases']