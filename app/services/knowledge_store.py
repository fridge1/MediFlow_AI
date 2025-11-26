from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.knowledge import KBItem


class KnowledgeStoreService:
    @staticmethod
    async def store_items(db: AsyncSession, collection: str, pairs: List[Dict[str, Any]]) -> int:
        try:
            bind = db.get_bind()
            async with bind.begin() as conn:
                from app.core.database import Base
                await conn.run_sync(Base.metadata.create_all)
        except Exception:
            pass
        items = [
            KBItem(
                collection=collection,
                backend_pk=str(p["backend_pk"]),
                text=p.get("text", ""),
                meta=p.get("metadata", {}),
            )
            for p in pairs
        ]
        try:
            for item in items:
                db.add(item)
            await db.flush()
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass
            return len(pairs)
        return len(pairs)

    @staticmethod
    async def query_by_pks(db: AsyncSession, collection: str, pks: List[str]) -> List[Dict[str, Any]]:
        try:
            result = await db.execute(
                select(KBItem).where(KBItem.collection == collection, KBItem.backend_pk.in_(pks))
            )
            out: List[Dict[str, Any]] = []
            for item in result.scalars().all():
                out.append({
                    "backend_pk": item.backend_pk,
                    "text": item.text,
                    "metadata": item.meta,
                })
            return out
        except Exception:
            return []

    @staticmethod
    async def delete_collection(db: AsyncSession, collection: str) -> int:
        try:
            res = await db.execute(delete(KBItem).where(KBItem.collection == collection))
            return res.rowcount or 0
        except Exception:
            return 0
