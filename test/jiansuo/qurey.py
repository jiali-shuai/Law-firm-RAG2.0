from config import setup_env
from qianru.BGE import encode_query_bge_m3, model
from database.milvus import hybrid_search_bge_m3
setup_env()

"""查询函数"""
def query(question: str, dense_top_k, sparse_top_k, alpha, collection_name=None):
    query_dense, query_sparse = encode_query_bge_m3(question, model)
    results = hybrid_search_bge_m3(query_dense, query_sparse, dense_top_k, sparse_top_k, alpha, collection_name=collection_name)
    return results
