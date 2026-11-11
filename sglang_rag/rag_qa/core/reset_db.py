from pymilvus import connections, utility
from base.config  import config

# 连接 Milvus
connections.connect(alias="default", host=config.MILVUS_HOST, port=config.MILVUS_PORT)

collection_name = "nutrition_docs"

# 检查并删除集合
if utility.has_collection(collection_name):
    utility.drop_collection(collection_name)
    print(f"🗑️ 集合 {collection_name} 已成功销毁！")
else:
    print(f"⚠️ 集合 {collection_name} 不存在，无需销毁。")