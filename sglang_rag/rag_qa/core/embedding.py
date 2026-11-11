from sentence_transformers import SentenceTransformer
import os

class BGEEmbedding:
    def __init__(self):
        CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # 注意路径层级，这里指向 rag_qa/models/bge-m3
        model_path = os.path.join(CURRENT_DIR, "models", "bge-m3")
        print("Loading BGE-M3 from:", model_path)
        self.model = SentenceTransformer(model_path)

    def get_embedding(self, text):
        return self.model.encode([text]).tolist()[0]