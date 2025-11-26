from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import vector_service
from app.services.knowledge_store import KnowledgeStoreService
import hmac
import hashlib
import json
from app.celery_app import embed_document

router = APIRouter(prefix="/knowledge", tags=["知识库"])


@router.post("/docs")
async def upload_doc(payload: dict, db: AsyncSession = Depends(get_db)):
    if not settings.ENABLE_KB:
        raise HTTPException(status_code=501, detail="知识库未启用")
    text = str(payload.get("text", ""))
    doc_id = payload.get("doc_id") or str(abs(hash(text)))
    return {"doc_id": doc_id}


@router.post("/upsert")
async def upsert_vectors(payload: dict, db: AsyncSession = Depends(get_db)):
    if not settings.ENABLE_KB:
        raise HTTPException(status_code=501, detail="知识库未启用")
    collection = payload.get("collection", "default")
    texts = payload.get("texts", [])
    metas_in = payload.get("metadatas", [{} for _ in texts])
    metas = [{**m, "text": t} for t, m in zip(texts, metas_in)]
    if payload.get("async"):
        res = embed_document.delay(texts)
        if settings.CELERY_ALWAYS_EAGER:
            vectors = res.get()
        else:
            return {"task_id": res.id}
    else:
        vectors = await EmbeddingService.embed(texts)
    await vector_service.create_collection(collection, len(vectors[0]) if vectors else 0)
    ids = []
    if hasattr(vector_service, "upsert_with_ids"):
        ids = await vector_service.upsert_with_ids(collection, vectors, metas)
    else:
        await vector_service.upsert(collection, vectors, metas)
    if ids:
        pairs = [{"backend_pk": pk, "text": t, "metadata": m} for pk, t, m in zip(ids, texts, metas_in)]
        await KnowledgeStoreService.store_items(db, collection, pairs)
    return {"count": len(texts)}


@router.post("/query")
async def query_vectors(payload: dict, db: AsyncSession = Depends(get_db)):
    if not settings.ENABLE_KB:
        raise HTTPException(status_code=501, detail="知识库未启用")
    collection = payload.get("collection", "default")
    query_text = payload.get("query", "")
    top_k = int(payload.get("top_k", 5))
    offset = int(payload.get("offset", 0))
    limit = int(payload.get("limit", top_k))
    filters = payload.get("filters", {})
    qv = (await EmbeddingService.embed([query_text]))[0]
    items = await vector_service.query(collection, qv, top_k=top_k)
    pks = [i.get("pk") for i in items if i.get("pk") is not None]
    if pks:
        mapped = await KnowledgeStoreService.query_by_pks(db, collection, pks)
        merged: list = []
        for it in items:
            pk = it.get("pk")
            if pk is None:
                merged.append(it)
            else:
                found = next((m for m in mapped if m["backend_pk"] == pk), None)
                if found:
                    merged.append({**found, "score": it.get("score")})
                else:
                    base_meta = {k: v for k, v in it.items() if k not in ("pk", "score")}
                    merged.append({"backend_pk": pk, "text": "", "metadata": base_meta, "score": it.get("score")})
        if filters:
            def match(m):
                meta = m.get("metadata") or {}
                for k, v in filters.items():
                    if meta.get(k) != v:
                        return False
                return True
            merged = [m for m in merged if match(m)]
        sliced = merged[offset:offset+limit]
        return {"items": sliced}
    if filters:
        def match2(m):
            meta = m.get("metadata") or {}
            for k, v in filters.items():
                if meta.get(k) != v:
                    return False
            return True
        items = [m for m in items if match2(m)]
    sliced2 = items[offset:offset+limit]
    return {"items": sliced2}


@router.get("/collections")
async def list_collections(db: AsyncSession = Depends(get_db)):
    if not settings.ENABLE_KB:
        raise HTTPException(status_code=501, detail="知识库未启用")
    cols = await vector_service.list_collections()
    return {"items": cols}


@router.delete("/collections/{name}")
async def delete_collection(name: str, db: AsyncSession = Depends(get_db)):
    if not settings.ENABLE_KB:
        raise HTTPException(status_code=501, detail="知识库未启用")
    ok = await vector_service.delete_collection(name)
    await KnowledgeStoreService.delete_collection(db, name)
    return {"deleted": ok}
@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str, db: AsyncSession = Depends(get_db)):
    from celery.result import AsyncResult
    res = AsyncResult(task_id)
    return {"id": task_id, "state": str(res.state), "ready": bool(res.ready())}


@router.post("/tasks/{task_id}/callback")
async def task_callback(task_id: str, payload: dict, db: AsyncSession = Depends(get_db)):
    base = dict(payload)
    base.pop("signature", None)
    raw = json.dumps(base, separators=(",", ":"), ensure_ascii=False)
    sig = hmac.new(settings.KB_CALLBACK_SECRET.encode(), raw.encode(), hashlib.sha256).hexdigest()
    if payload.get("signature") and payload["signature"] != sig:
        raise HTTPException(status_code=401, detail="签名校验失败")
    collection = payload.get("collection", "default")
    vectors = payload.get("vectors", [])
    metas_in = payload.get("metadatas", [{} for _ in vectors])
    await vector_service.create_collection(collection, len(vectors[0]) if vectors else 0)
    ids = []
    if hasattr(vector_service, "upsert_with_ids"):
        ids = await vector_service.upsert_with_ids(collection, vectors, metas_in)
    else:
        await vector_service.upsert(collection, vectors, metas_in)
    if ids:
        pairs = [{"backend_pk": pk, "text": m.get("text", ""), "metadata": m} for pk, m in zip(ids, metas_in)]
        await KnowledgeStoreService.store_items(db, collection, pairs)
    return {"count": len(vectors)}
