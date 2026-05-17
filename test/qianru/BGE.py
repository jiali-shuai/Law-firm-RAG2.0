import numpy as np
from FlagEmbedding import BGEM3FlagModel
from config import BGE_MODEL_PATH, setup_env


setup_env()

model = BGEM3FlagModel(
    model_name_or_path=BGE_MODEL_PATH,
    use_fp16=False,
    device="cpu"
)

"""创建BGE-M3两种向量（稀疏+密集）"""
def create_bge_m3_embeddings(texts):
    print("🤖 创建BGE-M3两种向量（稀疏+密集）...")
    output = model.encode(
        texts,
        return_dense=True,
        return_sparse=True,
        return_colbert_vecs=False
    )
    dense_embeddings = np.array(output['dense_vecs'])
    sparse_embeddings = output['lexical_weights']
    return dense_embeddings, sparse_embeddings, model


"""编码查询为BGE-M3两种向量（稀疏+密集）"""
def encode_query_bge_m3(query, model):
    output = model.encode(
        [query],
        return_dense=True,
        return_sparse=True,
        return_colbert_vecs=False
    )
    query_dense = np.array(output['dense_vecs'][0])
    query_sparse = output['lexical_weights'][0]
    return query_dense, query_sparse
