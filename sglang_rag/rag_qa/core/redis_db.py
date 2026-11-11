import redis

class RedisCache:
    def __init__(self):
        # 连接你 Docker 里的 Milvus-Redis，并加上密码 1234
        self.client = redis.Redis(
            host='127.0.0.1',
            port=6379,
            db=0,
            password='1234',  # <--- 这里加上了你的真实密码
            decode_responses=True # 自动把字节转成字符串
        )
        # 测试连接
        self.client.ping()

    def get_answer(self, query):
        """查询缓存，如果存在返回答案，否则返回 None"""
        key = f"nutrition_faq:{query}"
        try:
            return self.client.get(key)
        except Exception:
            return None

    def set_answer(self, query, answer, expire_seconds=86400):
        """将答案写入缓存，默认过期时间 1 天 (86400秒)"""
        key = f"nutrition_faq:{query}"
        try:
            # 使用 setex 设置值和过期时间，防止 Redis 内存被撑爆
            self.client.setex(key, expire_seconds, answer)
        except Exception as e:
            print(f"Redis 写入失败: {e}")