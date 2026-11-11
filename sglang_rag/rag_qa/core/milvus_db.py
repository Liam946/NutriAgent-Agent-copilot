from pymilvus import connections, Collection

class MilvusDB:
    def __init__(self):
        # 连接 Milvus
        connections.connect(alias="default", host="127.0.0.1", port="19530")
        self.collection_name = "nutrition_docs"
        self.collection = Collection(name=self.collection_name)
        self.collection.load()

    def search(self, query_vector, limit=5):
        results = self.collection.search(
            data=[query_vector],
            anns_field="dense_vector",
            param={"metric_type": "COSINE", "params": {"nprobe": 10}},          #IVF-FLAT
            limit=limit,
            output_fields=["text", "source", "page"]  # 必须取出这几个字段
        )

        contexts = []
        for hit in results[0]:
            contexts.append({
                "text": hit.entity.get('text'),
                "source": hit.entity.get('source'),
                "page": hit.entity.get('page')
            })
        return contexts
