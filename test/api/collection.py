from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from database.milvus import list_collections_all, create_collection_entry

router = APIRouter()


class CollectionItem(BaseModel):
    name: str
    description: str


class ListCollectionsResponse(BaseModel):
    items: List[CollectionItem]


class CreateCollectionRequest(BaseModel):
    name: str
    description: str

"""服务在线检查"""
@router.get("/api/health")
def health():
    return {"status": "ok"}


"""列出所有集合"""
@router.get("/api/collections", response_model=ListCollectionsResponse)
def get_collections():
    items = list_collections_all()
    return ListCollectionsResponse(
        items=[CollectionItem(name=item["name"], description=item["description"]) for item in items]
    )

"""创建集合"""
@router.post("/api/collections")
def create_collection(req: CreateCollectionRequest):
    name = req.name.strip()
    description = req.description.strip()

    if not name:
        raise HTTPException(status_code=400, detail="名称不能为空")

    try:
        result = create_collection_entry(name, description)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return {
        "name": result["name"],
        "description": result["description"],
        "message": "创建成功",
    }
