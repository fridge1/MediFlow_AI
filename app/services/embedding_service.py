from typing import List
import hashlib

class EmbeddingService:
    @staticmethod
    async def embed(texts: List[str]) -> List[List[float]]:
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("BAAI/bge-small-zh-v1.5")
            vectors = model.encode(texts, normalize_embeddings=True)
            return [list(map(float, v)) for v in vectors]
        except Exception:
            dim = 384
            out = []
            for t in texts:
                h = hashlib.sha256(t.encode()).digest()
                seed = int.from_bytes(h[:4], "big")
                vec = []
                x = seed
                for _ in range(dim):
                    x = (1103515245 * x + 12345) & 0x7FFFFFFF
                    vec.append((x / 0x7FFFFFFF) * 2 - 1)
                out.append(vec)
            return out
