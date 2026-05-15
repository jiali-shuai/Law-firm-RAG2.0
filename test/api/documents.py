from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List
import os
import uuid

from llmodel.llm import CHAT_LLM


from database.milvus import insert_bge_m3_vectors
from database.registry import list_registered_files, register_file_source, delete_file_by_source, _next_source_id
    
from qianru.BGE import create_bge_m3_embeddings
from agent.FengKuaiAgent import SmartChunkerAgent

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


class FileInfo(BaseModel):
    file_name: str
    collection_name: str
    source_id: int


class ListFilesResponse(BaseModel):
    items: List[FileInfo]

"""列出所有已注册的文档"""
@router.get("/api/documents", response_model=ListFilesResponse)
def get_documents():
    items = list_registered_files()
    return ListFilesResponse(
        items=[FileInfo(file_name=item["file_name"], collection_name=item["collection_name"], source_id=item["source_id"]) for item in items]
    )

"""上传文档"""
@router.post("/api/documents/upload")
def upload_document(
    file: UploadFile = File(...),
    collection_name: str = Form(...),
):
    

    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    collection_name = collection_name.strip()
    if not collection_name:
        raise HTTPException(status_code=400, detail="集合名称不能为空")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".docx", ".pdf"):
        raise HTTPException(status_code=400, detail="仅支持 .docx 和 .pdf 格式")

    safe_name = f"{uuid.uuid4().hex}_{file.filename}"
    tmp_path = os.path.join(UPLOAD_DIR, safe_name)

    try:
        content = file.file.read()
        with open(tmp_path, "wb") as f:
            f.write(content)

        chat_llm = CHAT_LLM
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件失败: {e}")

    try:
        agent = SmartChunkerAgent(chat_llm)
        if ext == ".pdf":
            chunked_docs = agent.load_and_chunk_pdf(tmp_path, lower_percentile=25, upper_percentile=75)
        else:
            chunked_docs = agent.load_and_chunk_word(tmp_path, lower_percentile=25, upper_percentile=75)
        texts = [chunk.page_content for chunk in chunked_docs]

        if not texts:
            raise HTTPException(status_code=400, detail="文档无有效内容")

        dense_emb, sparse_emb, _ = create_bge_m3_embeddings(texts)
        source_id = _next_source_id()

        insert_bge_m3_vectors(texts, dense_emb, sparse_emb, collection_name=collection_name, source_id=source_id)
        register_file_source(file.filename, collection_name, source_id)

        return {
            "file_name": file.filename,
            "collection_name": collection_name,
            "source_id": source_id,
            "chunk_count": len(texts),
            "message": "上传并向量化成功",
        }
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

"""删除文档"""
@router.delete("/api/documents/{source_id}")
def delete_document(source_id: int):
    try:
        result = delete_file_by_source(source_id)
        return {
            "file_name": result["file_name"],
            "source_id": result["source_id"],
            "collection_name": result["collection_name"],
            "message": "删除成功",
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
