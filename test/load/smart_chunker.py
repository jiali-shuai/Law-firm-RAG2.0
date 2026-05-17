"""BGE-M3语义相似度智能分块 — 动态百分位法 + LLM灰色地带"""

from langchain_core.documents import Document
from FlagEmbedding import BGEM3FlagModel
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import json

from config import BGE_MODEL_PATH, setup_env
from agent.prompt_loader import load_prompt

setup_env()

_bge_model = None


def _get_bge_model():
    global _bge_model
    if _bge_model is None:
        _bge_model = BGEM3FlagModel(
            model_name_or_path=BGE_MODEL_PATH,
            use_fp16=False,
            device="cpu"
        )
    return _bge_model

"""计算余弦相似度"""
def _compute_cosine_similarity(vec1, vec2):
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot / (norm1 * norm2))

"""计算段落相似度"""
def _compute_paragraph_similarities(paragraphs):
    if len(paragraphs) <= 1:
        return [], None

    model = _get_bge_model()
    output = model.encode(
        paragraphs,
        return_dense=True,
        return_sparse=False,
        return_colbert_vecs=False
    )
    dense_vecs = np.array(output['dense_vecs'])

    similarities = []
    for i in range(len(dense_vecs) - 1):
        sim = _compute_cosine_similarity(dense_vecs[i], dense_vecs[i + 1])
        similarities.append(sim)

    return similarities, dense_vecs

"""动态百分位法"""
def _dynamic_percentile_thresholds(similarities, lower_percentile=25, upper_percentile=75):
    if not similarities:
        return 0.0, 0.0

    lower = np.percentile(similarities, lower_percentile)
    upper = np.percentile(similarities, upper_percentile)
    return float(lower), float(upper)

"""分类边界"""
def _classify_boundaries(similarities, lower_threshold, upper_threshold):
    boundaries = []
    for i, sim in enumerate(similarities):
        if sim < lower_threshold:
            boundaries.append(('split', i, sim))
        elif sim > upper_threshold:
            boundaries.append(('merge', i, sim))
        else:
            boundaries.append(('gray', i, sim))
    return boundaries


def _parse_json(text: str):
    text = text.strip()
    import re
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    if not text:
        raise ValueError("LLM 返回空内容")
    return json.loads(text)

"""LLM解决灰色地带"""
def _llm_resolve_gray_zones(paragraphs, gray_boundaries, chat_llm):
    prompt = load_prompt("gray_zone_chunker.txt")

    decisions = {}
    batch_size = 20

    pure_grays = [(t, i, s) for t, i, s in gray_boundaries if t == 'gray']

    batches = []
    for batch_start in range(0, len(pure_grays), batch_size):
        batches.append(pure_grays[batch_start:batch_start + batch_size])

    def _process_one_batch(batch):
        parts = []
        for local_idx, (_, idx, sim) in enumerate(batch):
            para_a = paragraphs[idx]
            para_b = paragraphs[idx + 1]
            parts.append(
                f"--- 段落对 #{local_idx} (原始索引={idx}, 相似度={sim:.3f}) ---\n"
                f"段落A:\n{para_a}\n\n"
                f"段落B:\n{para_b}"
            )
        context = "\n\n".join(parts)
        response = chat_llm.invoke([
            ("system", prompt),
            ("user", context)
        ])
        batch_decisions = _parse_json(response.content)
        return [(batch[item["idx"]][1], item.get("should_split", False))
                for item in batch_decisions]

    with ThreadPoolExecutor(max_workers=len(batches)) as executor:
        future_to_batch = {executor.submit(_process_one_batch, b): b for b in batches}
        for future in as_completed(future_to_batch):
            for global_idx, should_split in future.result():
                decisions[global_idx] = should_split

    return decisions

"""构建分块"""
def _build_chunks(paragraphs, boundaries, llm_decisions=None):
    if llm_decisions is None:
        llm_decisions = {}

    split_points = set()
    for boundary_type, idx, _ in boundaries:
        if boundary_type == 'split':
            split_points.add(idx)
        elif boundary_type == 'gray':
            if llm_decisions.get(idx, False):
                split_points.add(idx)

    chunks = []
    start = 0
    for i in range(len(paragraphs)):
        if i in split_points:
            chunk_text = "\n".join(paragraphs[start:i + 1])
            if chunk_text.strip():
                chunks.append(Document(page_content=chunk_text))
            start = i + 1

    if start < len(paragraphs):
        chunk_text = "\n".join(paragraphs[start:])
        if chunk_text.strip():
            chunks.append(Document(page_content=chunk_text))

    return chunks

"""智能分块"""
def smart_chunk_texts(texts, chat_llm=None, lower_percentile=25, upper_percentile=75):
    if len(texts) <= 1:
        return [Document(page_content=texts[0])] if texts else []

    similarities, _ = _compute_paragraph_similarities(texts)

    lower, upper = _dynamic_percentile_thresholds(similarities, lower_percentile, upper_percentile)
    print(f"动态阈值: 下界(P{lower_percentile})={lower:.3f}, 上界(P{upper_percentile})={upper:.3f}")

    boundaries = _classify_boundaries(similarities, lower, upper)
    gray_count = sum(1 for t, _, _ in boundaries if t == 'gray')
    split_count = sum(1 for t, _, _ in boundaries if t == 'split')
    merge_count = sum(1 for t, _, _ in boundaries if t == 'merge')
    print(f"边界分类: 明确分割={split_count}, 明确合并={merge_count}, 灰色地带={gray_count}")

    llm_decisions = {}
    if gray_count > 0 and chat_llm is not None:
        print(f"使用LLM处理 {gray_count} 个灰色地带...")
        gray_boundaries = [(t, i, s) for t, i, s in boundaries if t == 'gray']
        llm_decisions = _llm_resolve_gray_zones(texts, gray_boundaries, chat_llm)
        llm_split = sum(1 for v in llm_decisions.values() if v)
        llm_merge = sum(1 for v in llm_decisions.values() if not v)
        print(f"LLM判断: {llm_split} 个分割, {llm_merge} 个合并")
    elif gray_count > 0:
        print(f"有 {gray_count} 个灰色地带但未提供LLM，默认合并处理")

    chunks = _build_chunks(texts, boundaries, llm_decisions)
    print(f"分块后共 {len(chunks)} 个chunk")
    return chunks
