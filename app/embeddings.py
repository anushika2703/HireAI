"""sentence-transformers embeddings + FAISS cosine index over jobs."""
import threading

import faiss
import numpy as np

from . import config


class Embedder:
    def __init__(self, name: str = config.EMBED_MODEL):
        self.name, self._model, self._lock = name, None, threading.Lock()

    @property
    def model(self):
        with self._lock:
            if self._model is None:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.name)
        return self._model

    def embed(self, texts: list[str]) -> np.ndarray:
        v = self.model.encode(list(texts), normalize_embeddings=True,
                              convert_to_numpy=True, show_progress_bar=False)
        return np.asarray(v, dtype="float32")

    def embed_resume(self, text: str, words: int = 180, max_chunks: int = 12) -> np.ndarray:
        """MiniLM truncates long input, so embed chunks and average them."""
        w = text.split()
        chunks = [" ".join(w[i:i + words]) for i in range(0, len(w), words)][:max_chunks] or [""]
        v = self.embed(chunks).mean(axis=0)
        return (v / (np.linalg.norm(v) + 1e-9)).astype("float32")


def job_text(j: dict) -> str:
    return (f"{j['title']}. {j['description']} Required skills: {', '.join(j['required'])}. "
            f"Nice to have: {', '.join(j['nice'])}.")


class JobIndex:
    def __init__(self, embedder: Embedder):
        self.embedder, self.ids, self.index = embedder, [], None
        self._lock = threading.RLock()

    def build(self, jobs: list[dict]) -> None:
        with self._lock:
            if not jobs:
                self.ids, self.index = [], None
                return
            vecs = self.embedder.embed([job_text(j) for j in jobs])
            index = faiss.IndexFlatIP(vecs.shape[1])  # inner product == cosine on unit vectors
            index.add(vecs)
            self.ids, self.index = [j["id"] for j in jobs], index

    def search(self, vec: np.ndarray, k: int) -> list[tuple[int, float]]:
        with self._lock:
            if self.index is None:
                return []
            scores, idx = self.index.search(vec.reshape(1, -1), min(k, len(self.ids)))
            return [(self.ids[i], float(s)) for s, i in zip(scores[0], idx[0]) if i != -1]
