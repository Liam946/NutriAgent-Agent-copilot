# 该脚本用于: 配置文件管理.
import configparser
import os

# -------------通过代码获取config.ini文件的绝对路径，防止路径错误------------------------------------
abs_path = os.path.abspath(__file__)
parent_dir = os.path.dirname(abs_path)

# config.py 位于 sglang_rag/base/ 下，需要向上跳两层才到项目根目录 sglang_rag/
project_root = os.path.dirname(parent_dir)
config_file = os.path.join(project_root, 'config.ini')


class Config:
    def __init__(self, config_file=config_file):
        self.config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
        self.PROJECT_ROOT = project_root

        # 路径配置
        self.LOG_DIR = os.path.join(self.PROJECT_ROOT, 'logs')
        self.DATA_DIR = os.path.join(self.PROJECT_ROOT, 'rag_qa/data')
        self.MODELS_DIR = os.path.join(self.PROJECT_ROOT, 'rag_qa/models')

        if config_file is None:
            config_file = os.path.join(self.PROJECT_ROOT, 'config.ini')
        self.config.read(config_file, encoding='utf-8')

        # MySQL 配置 (你之前提到端口是80，如果报错记得去config.ini改成3306)
        self.MYSQL_HOST = os.getenv('MYSQL_HOST', self.config.get('mysql', 'host', fallback='127.0.0.1'))
        self.MYSQL_PORT = int(os.getenv('MYSQL_PORT', self.config.get('mysql', 'port', fallback=80)))
        self.MYSQL_USER = os.getenv('MYSQL_USER', self.config.get('mysql', 'user', fallback='root'))
        self.MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', self.config.get('mysql', 'password', fallback='123456'))
        self.MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', self.config.get('mysql', 'database', fallback='nutrition_db'))

        # Milvus 配置
        self.MILVUS_HOST = os.getenv('MILVUS_HOST', self.config.get('milvus', 'host', fallback='127.0.0.1'))
        self.MILVUS_PORT = os.getenv('MILVUS_PORT', self.config.get('milvus', 'port', fallback='19530'))
        self.MILVUS_COLLECTION_NAME = os.getenv('MILVUS_COLLECTION_NAME',
                                                self.config.get('milvus', 'collection_name', fallback='nutrition_docs'))

        # LLM 配置 (适配你本地的 SGLang)
        self.LLM_MODEL = self.config.get('llm', 'model', fallback='Qwen/Qwen3-0.6B')
        self.LLM_BASE_URL = self.config.get('llm', 'base_url', fallback='http://127.0.0.1:30000/v1')

        # 检索参数
        self.PARENT_CHUNK_SIZE = self.config.getint('retrieval', 'parent_chunk_size', fallback=1200)
        self.CHILD_CHUNK_SIZE = self.config.getint('retrieval', 'child_chunk_size', fallback=500)
        self.CHUNK_OVERLAP = self.config.getint('retrieval', 'chunk_overlap', fallback=50)
        self.RETRIEVAL_K = self.config.getint('retrieval', 'retrieval_k', fallback=8)

        # 模型具体路径
        self.BGE_M3_PATH = os.path.join(self.MODELS_DIR, 'bge-m3')


# 实例化配置，供全局调用
config = Config()

if __name__ == '__main__':
    # 测试配置是否读取成功
    print(f"MySQL: {config.MYSQL_HOST}:{config.MYSQL_PORT} / DB: {config.MYSQL_DATABASE}")
    print(f"Milvus: {config.MILVUS_HOST}:{config.MILVUS_PORT} / Collection: {config.MILVUS_COLLECTION_NAME}")
    print(f"LLM: {config.LLM_MODEL} @ {config.LLM_BASE_URL}")
    print(f"BGE模型路径: {config.BGE_M3_PATH}")
    print(f"检索 K 值: {config.RETRIEVAL_K}")