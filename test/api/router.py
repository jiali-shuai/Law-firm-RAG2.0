from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from config import setup_env
from database.milvus import get_client
from api import collection, documents, chat

setup_env()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        get_client()
        print("✅ Milvus 连接成功！")
    except Exception as e:
        print(f"⚠️ Milvus 连接失败: {e}")
    yield


app = FastAPI(title="RAG向量库管理系统", version="1.0.0", lifespan=lifespan)
api_router = APIRouter()

api_router.include_router(collection.router,tags=["集合"])
api_router.include_router(documents.router,tags=["文档"])
api_router.include_router(chat.router,tags=["咨询"])

app.include_router(api_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)






