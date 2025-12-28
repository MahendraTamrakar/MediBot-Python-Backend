import faiss
import numpy as np
import os
import pickle

class FaissVectorStore:
    def __init__(self, dim: int, index_path: str):
        self.dim = dim
        self.index_path = index_path

        if os.path.exists(index_path):
            self.index, self.metadata = self._load()
        else:
            quantizer = faiss.IndexFlatL2(dim)
            self.index = faiss.IndexIVFFlat(quantizer, dim, 100)
            self.index.train(np.random.random((1000, dim)).astype("float32"))
            self.metadata = []

    def add(self, vectors: list[list[float]], metadata: list[dict]):
        vectors_np = np.array(vectors).astype("float32")
        self.index.add(vectors_np)
        self.metadata.extend(metadata)
        self._save()

    def search(
        self,
        vector: list[float],
        user_id: str,
        chat_session_id: str,
        k: int = 5
    ):
        D, I = self.index.search(
            np.array([vector]).astype("float32"),
            k * 3  # over-fetch for filtering
        )

        results = []
        for idx in I[0]:
            if idx >= len(self.metadata):
                continue

            meta = self.metadata[idx]
            if (
                meta["user_id"] == user_id and
                meta["chat_session_id"] == chat_session_id
            ):
                results.append(meta)

            if len(results) >= k:
                break

        return results

    def _save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.index_path + ".meta", "wb") as f:
            pickle.dump(self.metadata, f)

    def _load(self):
        index = faiss.read_index(self.index_path)
        with open(self.index_path + ".meta", "rb") as f:
            metadata = pickle.load(f)
        return index, metadata