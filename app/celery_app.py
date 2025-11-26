from typing import List

from celery import Celery

from app.core.config import settings
from app.services.embedding_service import EmbeddingService

celery_app = Celery(
    "mediflow_ai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Run tasks eagerly configurable via settings
celery_app.conf.task_always_eager = settings.CELERY_ALWAYS_EAGER

@celery_app.task(name="embed_document")
def embed_document(texts: List[str]) -> List[List[float]]:
    import asyncio
    return asyncio.run(EmbeddingService.embed(texts))
