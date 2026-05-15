""" JSON 文件注册表 — 文件 → 集合 → source_id """
import os
import json
from database.milvus import get_client

FILE_REGISTRY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "file_registry.json"
)


"""加载文件注册表"""
def _load_registry() -> list:
    if os.path.exists(FILE_REGISTRY_PATH):
        with open(FILE_REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

"""保存文件注册表"""
def _save_registry(data: list):
    with open(FILE_REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

"""获取下一个 source_id"""
def _next_source_id() -> int:
    registry = _load_registry()
    if not registry:
        return 1
    return max(item.get("source_id", 0) for item in registry) + 1

"""注册文件源"""
def register_file_source(file_name: str, collection_name: str, source_id: int):
    registry = _load_registry()
    registry.append({
        "file_name": file_name,
        "collection_name": collection_name,
        "source_id": source_id,
    })
    _save_registry(registry)
    print(f"✅ 文件 '{file_name}' 注册完成，source_id={source_id} → 集合 '{collection_name}'")

"""列出所有注册的文件"""
def list_registered_files() -> list:
    return _load_registry()

"""删除文件源"""
def delete_file_by_source(source_id: int):
    registry = _load_registry()
    entry = None
    for item in registry:
        if item["source_id"] == source_id:
            entry = item
            break
    if not entry:
        raise ValueError(f"未找到 source_id={source_id} 的记录")

    source_id = entry["source_id"]
    collection_name = entry["collection_name"]

    client = get_client()
    if client.has_collection(collection_name):
        client.load_collection(collection_name)
        filter_expr = f"source_id == {source_id}"
        try:
            client.delete(collection_name=collection_name, filter=filter_expr)
            print(f"✅ 从集合 '{collection_name}' 删除 source_id={source_id} 的所有chunk")
        except Exception as e:
            print(f"⚠️ 删除chunk失败: {e}")
            raise RuntimeError(f"删除chunk失败: {e}")

    registry = [item for item in registry if item["source_id"] != source_id]
    _save_registry(registry)
    print(f"✅ source_id={source_id} 注册记录已删除")

    return {"file_name": entry["file_name"], "source_id": source_id, "collection_name": collection_name}
