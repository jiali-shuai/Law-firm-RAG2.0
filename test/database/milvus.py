from pymilvus import MilvusClient, FieldSchema, CollectionSchema, DataType
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict,Optional
from config import MILVUS_URI, COLLECTION_NAME

RRF_K = 30# RRF 融合参数
"""连接Milvus数据库"""
client = None
def get_client():
    global client
    if client is None:
        client = MilvusClient(uri=MILVUS_URI,timeout=6)
    return client


"""""""""""""""""""""""""""""""""插入数据阶段"""""""""""""""""""""""""""""""""
"""创建新集合（名称+描述）"""
def create_collection_entry(collection_name: str, description: str):

    client = get_client()

    if client.has_collection(collection_name):
        raise ValueError(f"集合 '{collection_name}' 已存在")

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=5000),
        FieldSchema(name="dense_vector", dtype=DataType.FLOAT_VECTOR, dim=1024),
        FieldSchema(name="sparse_vector", dtype=DataType.SPARSE_FLOAT_VECTOR),
        FieldSchema(name="source_id", dtype=DataType.INT64),
    ]

    schema = CollectionSchema(fields, description=description)
    client.create_collection(collection_name, schema=schema)

    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="dense_vector",
        index_type="IVF_FLAT",
        metric_type="COSINE",
        params={"nlist": 128},
    )
    index_params.add_index(
        field_name="sparse_vector",
        index_type="SPARSE_INVERTED_INDEX",
        metric_type="IP",
        params={"nlist": 128},
    )
    client.create_index(collection_name, index_params)
    client.load_collection(collection_name)
    print(f"✅ 集合 '{collection_name}' 创建并加载完成！")

    return {"name": collection_name, "description": description}

"""插入BGE-M3两种向量到Milvus"""
def insert_bge_m3_vectors(
    texts: List[str],
    dense_embeddings: np.ndarray,
    sparse_embeddings: List[Dict[int, float]],
    collection_name: Optional[str] = None,
    source_id: int = 0,
):

    target = collection_name or COLLECTION_NAME
    client = get_client()

    if not client.has_collection(target):
        raise ValueError(f"集合 '{target}' 不存在，请先在集合管理页创建")
    client.load_collection(target)

    desc = client.describe_collection(target)
    field_names = {f["name"] for f in desc.get("fields", [])}
    if "dense_vector" not in field_names or "sparse_vector" not in field_names:
        raise ValueError(f"集合 '{target}' 缺少向量字段，不能写入 chunk")

    dense_data = dense_embeddings
    sparse_data = sparse_embeddings

    data = [
        {
        "dense_vector": dense_data[i],
        "sparse_vector": sparse_data[i],
        "text": texts[i],
        "source_id": source_id
        }
        for i in range(len(texts))
    ]

    insert_result = client.insert(target, data)
    chunk_ids = [int(i) for i in insert_result["ids"]]
    print(f"✅ 成功插入 {len(texts)} 条BGE-M3向量数据！")

    return chunk_ids





"""""""""""""""""""""""""""""""""检索数据阶段"""""""""""""""""""""""""""""""""
"""搜索密集向量"""
def search_dense_vectors(query_dense, dense_top_k,collection_name:Optional[str]=None):
    target = collection_name or COLLECTION_NAME
    client = get_client()
    client.load_collection(target)

    results = client.search(
        target,
        data=query_dense,
        anns_field="dense_vector",
        search_params={"metric_type": "COSINE", "params": {"nprobe": 15}},
        limit=dense_top_k,
        output_fields=["text"]
    )
    return results



"""搜索稀疏向量"""
def search_sparse_vectors(query_sparse, sparse_top_k,collection_name:Optional[str]=None):
    target = collection_name or COLLECTION_NAME
    client = get_client()
    client.load_collection(target)
    
    results = client.search(
        target,
        data=query_sparse,
        anns_field="sparse_vector",
        search_params={"metric_type": "IP", "params": {}},
        limit=sparse_top_k,
        output_fields=["text"]
    )
    return results


"""将密集嵌入转换为Milvus格式"""
def dense_to_milvus_format(query_dense: np.ndarray) -> List[List[float]]:
    
    if len(query_dense.shape) == 1:
        return [query_dense.tolist()]
    return query_dense.tolist()


"""将稀疏向量转换为Milvus格式"""
def sparse_to_milvus_format(query_sparse: List[Dict[int, float]]):

    query_sparse = [query_sparse]
    return query_sparse



""" BGE-M3 双路混合检索（dense + sparse 并发 + RRF 融合）"""

def hybrid_search_bge_m3(query_dense, query_sparse, dense_top_k, sparse_top_k, alpha,collection_name:Optional[str]=None):
    dense_query = dense_to_milvus_format(query_dense)
    sparse_query = sparse_to_milvus_format(query_sparse)

    with ThreadPoolExecutor(max_workers=2) as executor:
        dense_future = executor.submit(search_dense_vectors, dense_query, dense_top_k, collection_name)
        sparse_future = executor.submit(search_sparse_vectors, sparse_query, sparse_top_k, collection_name)
        dense_res = dense_future.result()
        sparse_res = sparse_future.result()

    doc_dict = {}

    for rank, hit in enumerate(dense_res[0]):
        doc_dict[hit.id] = {
            "text": hit.entity["text"],
            "rrf_score": alpha / (RRF_K + rank + 1)
        }

    for rank, hit in enumerate(sparse_res[0]):
        rrf_score = (1 - alpha) / (RRF_K + rank + 1)
        if hit.id in doc_dict:
            doc_dict[hit.id]["rrf_score"] += rrf_score
        else:
            doc_dict[hit.id] = {
                "text": hit.entity["text"],
                "rrf_score": rrf_score
            }

    combined = [
        {"id": doc_id, "text": info["text"], "distance": info["rrf_score"]}
        for doc_id, info in doc_dict.items()
    ]
    combined = sorted(combined, key=lambda x: x["distance"], reverse=True)
    return [combined[:dense_top_k + sparse_top_k]]




"""""""""""""""""""""""""""""""""返回数据阶段"""""""""""""""""""""""""""""""""
"""列出所有集合（名称+描述）"""
def list_collections_all():
    client = get_client()
    names = client.list_collections()
    result = []
    for name in names:
        try:
            info = client.describe_collection(name)
            result.append({
                "name": name,
                "description": info.get("description", ""),
            })
        except Exception:
            result.append({"name": name, "description": ""})
    return result





