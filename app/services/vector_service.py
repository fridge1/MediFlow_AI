from typing import List, Dict, Any, Tuple
import math
from app.core.config import settings


class MemoryVectorService:
    def __init__(self):
        self.store: Dict[str, List[Tuple[List[float], Dict[str, Any]]]] = {}

    async def create_collection(self, name: str, dim: int) -> bool:
        self.store.setdefault(name, [])
        return True

    async def list_collections(self) -> List[str]:
        return list(self.store.keys())

    async def delete_collection(self, name: str) -> bool:
        if name in self.store:
            del self.store[name]
            return True
        return False

    async def upsert(self, name: str, vectors: List[List[float]], metadatas: List[Dict[str, Any]]) -> int:
        items = self.store.setdefault(name, [])
        for v, m in zip(vectors, metadatas):
            items.append((v, m))
        return len(vectors)

    async def upsert_with_ids(self, name: str, vectors: List[List[float]], metadatas: List[Dict[str, Any]]) -> List[str]:
        items = self.store.setdefault(name, [])
        ids: List[str] = []
        for v, m in zip(vectors, metadatas):
            idx = len(items)
            items.append((v, m))
            ids.append(str(idx))
        return ids

    async def query(self, name: str, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        items = self.store.get(name, [])
        def cosine(a: List[float], b: List[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b))
            na = math.sqrt(sum(x * x for x in a))
            nb = math.sqrt(sum(y * y for y in b))
            if na == 0 or nb == 0:
                return 0.0
            return dot / (na * nb)
        scored = [(cosine(query_vector, v), m, str(i)) for i, (v, m) in enumerate(items)]
        scored.sort(key=lambda x: x[0], reverse=True)
        out = []
        for score, meta, pk in scored[:top_k]:
            r = dict(meta)
            r["score"] = float(score)
            r["pk"] = pk
            out.append(r)
        return out


class MilvusVectorService:
    def __init__(self):
        # Lazy import; fallback if not available
        self._available = False
        try:
            from pymilvus import connections
            self._connections = connections
            self._available = True
        except Exception:
            self._connections = None

    async def create_collection(self, name: str, dim: int) -> bool:
        if not self._available:
            return False
        from pymilvus import utility, CollectionSchema, FieldSchema, DataType, Collection
        if utility.has_collection(name):
            return True
        fields = [
            FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
        ]
        schema = CollectionSchema(fields)
        Collection(name, schema)
        return True

    async def list_collections(self) -> List[str]:
        if not self._available:
            return []
        from pymilvus import utility
        return utility.list_collections()

    async def delete_collection(self, name: str) -> bool:
        if not self._available:
            return False
        from pymilvus import utility
        if utility.has_collection(name):
            utility.drop_collection(name)
            return True
        return False

    async def upsert(self, name: str, vectors: List[List[float]], metadatas: List[Dict[str, Any]]) -> int:
        if not self._available:
            return 0
        from pymilvus import Collection
        col = Collection(name)
        data = [vectors]
        col.insert([data[0]])
        return len(vectors)

    async def upsert_with_ids(self, name: str, vectors: List[List[float]], metadatas: List[Dict[str, Any]]) -> List[str]:
        if not self._available:
            return []
        from pymilvus import Collection
        col = Collection(name)
        mr = col.insert([vectors])
        return [str(pk) for pk in getattr(mr, "primary_keys", [])]

    async def query(self, name: str, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        if not self._available:
            return []
        from pymilvus import Collection
        col = Collection(name)
        res = col.search([query_vector], "embedding", params={"metric_type": "COSINE"}, limit=top_k, output_fields=["pk"])
        out: List[Dict[str, Any]] = []
        for hits in res:
            for h in hits:
                out.append({"pk": int(h.id), "score": float(h.distance)})
        return out


# Default to memory implementation for local/tests
def get_vector_service():
    if settings.VECTOR_BACKEND == "milvus":
        svc = MilvusVectorService()
        if svc._available:
            try:
                from pymilvus import connections
                connections.connect(host=settings.MILVUS_HOST, port=str(settings.MILVUS_PORT), user=settings.MILVUS_USER, password=settings.MILVUS_PASSWORD)
                return svc
            except Exception:
                pass
    return MemoryVectorService()

vector_service = get_vector_service()
