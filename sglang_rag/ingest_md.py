import os
import re
import logging
from logging.handlers import TimedRotatingFileHandler
import jieba
from pymilvus import connections, utility, FieldSchema, CollectionSchema, DataType, Collection
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from base.config import config

# ================= 0. 配置日志 =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, "ingest.log")

logger = logging.getLogger("IngestLogger")
logger.setLevel(logging.INFO)

if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)

    file_handler = TimedRotatingFileHandler(LOG_FILE, when="midnight", interval=1, backupCount=7, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)


# ================= 0.5 核心新增：正则清洗模块 =================
def clean_text(text):
    """
    对提取出的 Markdown 文本进行清洗，去除无意义的碎块。
    """
    # 1. 去除常见的页眉页脚（如：第 x 页，共 y 页，或者单独的数字）
    text = re.sub(r'第\s*\d+\s*页(\s*共\s*\d+\s*页)?', '', text)

    # 2. 去除 Markdown 的图片链接（因为纯文本大模型读不到图片）
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)

    # 3. 将连续 3 个及以上的换行压缩为 2 个（保留段落结构）
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 4. 按行处理：过滤掉极短的碎块、纯数字、纯符号
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        # 如果是空行，保留（用于后面切段落）
        if not stripped:
            cleaned_lines.append("")
            continue

        # 过滤掉长度小于 5 的无意义短句（比如孤立字符、乱码）
        # 但如果是 Markdown 标题（#），即使短也保留
        if len(stripped) < 5 and not stripped.startswith('#'):
            continue

        # 过滤掉纯数字或者纯标点符号的行
        if re.fullmatch(r'[\d\W_]+', stripped):
            continue

        cleaned_lines.append(stripped)

    return '\n'.join(cleaned_lines)


# ================= 1. 读取与带章节识别的切分 =================
def truncate_by_bytes(text, max_bytes):
    """按 UTF-8 字节数截断字符串，保证不超过 Milvus VARCHAR 上限"""
    while max_bytes > 0 and len(text.encode('utf-8')) > max_bytes:
        text = text[:len(text) - 100]
    return text


def hard_split_long_text(text, chunk_size):
    """对超长段落按句子边界强制二次拆分，保证每块不超过 chunk_size 字符"""
    if len(text) <= chunk_size:
        return [text]
    pieces = re.split(r'(?<=[。！？；\n])', text)
    parts, cur = [], ""
    for piece in pieces:
        if len(cur) + len(piece) <= chunk_size:
            cur += piece
        else:
            if cur:
                parts.append(cur)
            if len(piece) > chunk_size:
                for i in range(0, len(piece), chunk_size):
                    parts.append(piece[i:i + chunk_size])
                cur = ""
            else:
                cur = piece
    if cur:
        parts.append(cur)
    return parts


def extract_text_from_md(md_path):
    logger.info(f"正在读取文件: {os.path.basename(md_path)}")
    with open(md_path, "r", encoding="utf-8") as f:
        return f.read()


def split_text_with_headers(text, chunk_size=500, overlap=50):
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    current_header = "前言/概述"  # 默认标题

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if para.startswith('#'):
            current_header = para.lstrip('#').strip()

        if len(current_chunk) + len(para) <= chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append({"text": current_chunk.strip(), "header": current_header})
            current_chunk = current_chunk[-overlap:] + para + "\n\n" if overlap > 0 else para + "\n\n"

    if current_chunk:
        chunks.append({"text": current_chunk.strip(), "header": current_header})

    safe_chunks = []
    for c in chunks:
        for piece in hard_split_long_text(c["text"], chunk_size):
            safe_chunks.append({"text": piece, "header": c["header"]})
    return safe_chunks


# ================= 2. 主流程 =================
def main():
    try:
        logger.info("正在连接 Milvus...")
        connections.connect(alias="default", host=config.MILVUS_HOST, port=config.MILVUS_PORT)
        collection_name = "nutrition_docs"

        if not utility.has_collection(collection_name):
            logger.info(f"集合 {collection_name} 不存在，正在创建 Schema...")
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="partition_key", dtype=DataType.INT64, is_partition_key=True),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=255),
                FieldSchema(name="page", dtype=DataType.VARCHAR, max_length=255),
                FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="dense_vector", dtype=DataType.FLOAT_VECTOR, dim=1024),
                FieldSchema(name="sparse_vector", dtype=DataType.SPARSE_FLOAT_VECTOR)
            ]
            schema = CollectionSchema(fields, description="企业级营养学知识库")
            collection = Collection(name=collection_name, schema=schema)

            logger.info("正在建立双路索引...")
            collection.create_index(field_name="dense_vector",
                                    index_params={"metric_type": "COSINE", "index_type": "IVF_FLAT",
                                                  "params": {"nlist": 128}})
            collection.create_index(field_name="sparse_vector",
                                    index_params={"index_type": "SPARSE_INVERTED_INDEX", "metric_type": "IP"})
        else:
            logger.info(f"集合 {collection_name} 已存在，直接追加数据。")
            collection = Collection(name=collection_name)

        collection.load()

        logger.info(f"正在加载本地 BGE-M3 模型: {config.BGE_M3_PATH}")
        model = SentenceTransformer(config.BGE_M3_PATH)

        md_path_1 = r"E:\workspace\EduRAG\SGLangRAG\sglang_rag\《中国居民膳食指南（2022年版）》.md"

        doc_metadata = {
            md_path_1: {"category": "膳食指南"},
        }

        all_data = []
        for md_file in [md_path_1]:
            if os.path.exists(md_file):
                raw_text = extract_text_from_md(md_file)

                # 核心修改：在切分前，先进行正则清洗！
                logger.info("正在进行正则清洗，过滤无意义的碎块...")
                cleaned_text = clean_text(raw_text)

                # 用清洗后的文本去切分
                chunk_objs = split_text_with_headers(cleaned_text, chunk_size=500, overlap=50)
                source_name = os.path.basename(md_file)
                category_name = doc_metadata[md_file]["category"]

                for obj in chunk_objs:
                    all_data.append({
                        "text": obj["text"],
                        "partition_key": 1,
                        "source": source_name,
                        "page": obj["header"],
                        "category": category_name
                    })
            else:
                logger.warning(f"⚠️ 找不到文件: {md_file}")

        logger.info(f"经清洗和切分，共保留 {len(all_data)} 个高质量文本块。正在计算向量...")
        texts = [item["text"] for item in all_data]

        MAX_TEXT_BYTES = 60000
        too_long = [i for i, t in enumerate(texts) if len(t.encode('utf-8')) > MAX_TEXT_BYTES]
        if too_long:
            logger.warning(f"发现 {len(too_long)} 个超长块，将按字节截断: {too_long[:5]}...")
            texts = [truncate_by_bytes(t, MAX_TEXT_BYTES) for t in texts]

        dense_vectors = model.encode(texts, batch_size=16, show_progress_bar=True).tolist()

        logger.info("正在进行 jieba 分词与 BM25 计算...")
        tokenized_corpus = [list(jieba.cut(text)) for text in texts]
        bm25 = BM25Okapi(tokenized_corpus)

        sparse_vectors = []
        for tokens in tokenized_corpus:
            sparse_dict = {}
            for word in set(tokens):
                score = bm25.idf.get(word, 0)
                if score > 0:
                    word_id = abs(hash(word)) % 250000
                    sparse_dict[word_id] = float(score)
            sparse_vectors.append(sparse_dict)

        logger.info("正在构建列式数据并入库...")
        partition_keys = [item["partition_key"] for item in all_data]
        sources = [item["source"] for item in all_data]
        pages = [item["page"] for item in all_data]
        categories = [item["category"] for item in all_data]

        collection.insert([
            partition_keys, texts, sources, pages, categories, dense_vectors, sparse_vectors
        ])

        collection.flush()
        logger.info(f"✅ 入库完成！当前知识库总块数：{collection.num_entities}")

    except Exception as e:
        logger.error(f"❌ 入库过程中发生异常: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()