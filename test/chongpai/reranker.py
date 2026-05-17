from FlagEmbedding import FlagReranker
from config import RERANKER_MODEL_PATH, setup_env


setup_env()

reranker = FlagReranker(
    RERANKER_MODEL_PATH,
    use_fp16=False,
    device="cpu"
)

"""使用BGE Reranker进行重排序"""
def bge_rerank(query: str, documents: list, final_top_k):
    pairs = [[query, doc.get("text", "")] for doc in documents] # 生成查询-文档对
    scores = reranker.compute_score(pairs, normalize=True)
    ranked = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
    return [{"text": doc.get("text", ""), "rerank_score": score}
            for doc, score in ranked[:final_top_k]]
