import os
import faiss
import numpy as np

class FaissService:
    def __init__(self, base_path="faiss_store"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def _index_path(self, uid, session_id):
        return f"{self.base_path}/{uid}_{session_id}.index"

    def add_documents(self, uid, session_id, embeddings):
        dim = len(embeddings[0])
        index = faiss.IndexFlatL2(dim)
        index.add(np.array(embeddings).astype("float32"))
        faiss.write_index(index, self._index_path(uid, session_id))

    def search(self, uid, session_id, query_embedding, k=5):
        path = self._index_path(uid, session_id)
        if not os.path.exists(path):
            return []

        index = faiss.read_index(path)
        _, results = index.search(
            np.array([query_embedding]).astype("float32"), k
        )
        return results[0].tolist()

    def has_documents(self, uid, session_id) -> bool:
        """Check if any documents exist for this user/session."""
        # Check for standard index
        path = self._index_path(uid, session_id)
        if os.path.exists(path):
            return True
        # Check for document index (created by chat_document_controller)
        doc_path = f"{self.base_path}/{uid}_{session_id}_docs.index"
        return os.path.exists(doc_path)

    def delete(self, uid, session_id):
        path = self._index_path(uid, session_id)
        if os.path.exists(path):
            os.remove(path)
    
    def delete_all_for_user(self, firebase_uid: str):
        for file in os.listdir(self.base_path):
            if file.startswith(f"{firebase_uid}_") and file.endswith(".index"):
                os.remove(os.path.join(self.base_path, file))