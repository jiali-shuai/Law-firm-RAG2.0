import json
from langchain_core.tools import tool

from chongpai.reranker import bge_rerank
from jiansuo.qurey import query 

"""查询函数工具"""
@tool
def search_knowledge_base(
    search_query: str,
    dense_top_k: int,
    sparse_top_k: int,
    alpha: float,
    collection_name: str,
) -> str:
    """
    在知识库中检索相关法律文档（召回阶段）。
    当你需要查找相关案例、法律条文、司法解释等信息时调用此工具。
    参数说明：
    - search_query: 检索查询字符串，应包含关键法律要素
    - dense_top_k: 语义检索返回数量
    - sparse_top_k: 关键词检索返回数量
    - alpha: 混合权重，越大越偏语义
    - collection_name: 知识库名称（minshi/xingshi/xingzheng）
    返回：JSON格式的相关文档列表，包含id和text字段
    """
    results = query(search_query, dense_top_k, sparse_top_k, alpha, collection_name=collection_name)
    docs = []
    for item in results[0]:
        docs.append({"id": item.get("id", ""), "text": item.get("text", "")})
    return json.dumps(docs, ensure_ascii=False, indent=2)

"""重排函数工具"""
@tool
def rerank_documents(
    query: str,
    documents_json: str,
    final_top_k: int,
) -> str:
    """
    对已检索到的文档进行重排序（精排阶段）。
    当检索到多份文档后，调用此工具对其进行相关性重排，选出最相关的 top_k 篇。
    参数说明：
    - query: 用户原始诉求或核心检索问题
    - documents_json: 待重排的文档列表的JSON字符串，每项需包含id和text字段
    - final_top_k: 最终保留的文档数量，建议5-8
    返回：JSON格式的重排后文档列表，包含text和rerank_score字段
    """
    docs = json.loads(documents_json)
    reranked = bge_rerank(query, docs, final_top_k)
    return json.dumps(reranked, ensure_ascii=False, indent=2)
