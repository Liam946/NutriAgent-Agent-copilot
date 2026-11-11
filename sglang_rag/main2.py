from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from base.config import config
from rag_qa.core.embedding import BGEEmbedding
from rag_qa.core.milvus_db import MilvusDB
from rag_qa.core.llm import SGLangClient
from rag_qa.core.mysql_db import MySQLDB
from base.router import IntentRouter

from rag_qa.tools.html_generator import generate_html_from_rag

app = FastAPI(title="营养健康 Copilot API (LangChain版)")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"],
                   allow_headers=["*"])

output_dir = os.path.join(config.PROJECT_ROOT, "output_htmls")
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
app.mount("/reports", StaticFiles(directory=output_dir), name="reports")

print("正在初始化系统...")
embedder = BGEEmbedding()
db = MilvusDB()
llm = SGLangClient()
mysql_db = MySQLDB()
router = IntentRouter()

# ============================================================
# RAG prompt：允许如实说明资料不足，禁止编造
# ============================================================
rag_prompt_template = ChatPromptTemplate.from_messages([
    ("system", "你是一个专业的营养师。请认真阅读以下参考资料，然后回答用户的问题。\n\n【参考资料】\n{context}"),
    ("human",
     "{query}\n\n【回答要求】\n"
     "1. 如果参考资料中提到了相关内容，请提取出来并总结。\n"
     "2. 如果参考资料确实没有覆盖该问题，请明确说明“根据现有资料无法完整回答”，不要编造。\n"
     "3. 回答必须严格基于参考资料，不得引入资料外的信息。\n"
     "4. 请分点作答，保持专业。")
])

chitchat_prompt_template = ChatPromptTemplate.from_messages([
    ("system", "你是一个友好的营养健康助手。请简短、礼貌地回答用户；"
               "如果用户的问题与营养健康无关，请礼貌说明你只能回答营养健康相关问题。"),
    ("human", "{query}")
])

# ============================================================
# 边界/闲聊关键词兜底（放在 IntentRouter 之前）
# ============================================================
EDGE_WORDS = [
    "写诗", "写一首", "作诗", "笑话", "讲个故事", "讲故事", "唱歌",
    "你喜欢", "你喜欢吃什么", "天气", "翻译", "写代码", "编程",
    "讲个笑话", "聊聊天", "陪我聊"
]
EDGE_REPLY = "我是营养健康助手，这个问题我帮不上忙～不过饮食营养相关的问题我都能帮你解答。"


class ChatRequest(BaseModel):
    query: str


def _is_edge_query(query: str) -> bool:
    return any(w in query for w in EDGE_WORDS)


@app.post("/api/chat")
async def chat(request: ChatRequest):
    query = request.query
    print(f"\n👤 用户 Query: {query}")

    # ================= 1. 报告生成意图 =================
    REPORT_PAT = re.compile(r"(生成|做|出|来).{0,6}(报告|PPT|ppt|方案)")
    is_report = bool(REPORT_PAT.search(query)) and (
        ("营养" in query) or ("饮食" in query) or ("健康" in query) or len(query) <= 20
    )
    if is_report:
        print("📊 识别到生成报告意图，正在调用 RAG 提取大纲...")
        search_query = (query.replace("生成PPT", "").replace("做个ppt", "")
                        .replace("帮我", "").replace("生成报告", "")
                        .replace("生成方案", "").replace("做方案", "").strip())
        if not search_query:
            search_query = "高血压患者的一日三餐建议"

        query_vector = embedder.get_embedding(search_query)
        contexts = db.search(query_vector, limit=3)
        context_text = "\n\n".join([c.get("text", "") for c in contexts])

        html_prompt = f"""请根据以下资料，提取核心内容，生成一份结构清晰的营养报告。
要求：
1. 必须包含“一、核心建议”和“二、注意事项”两个模块。
2. 使用 Markdown 格式，使用短句，多使用加粗（**重点**）和无序列表（- 列表项）。
3. 字数控制在300字左右，适合在网页上阅读。

【资料】\n{context_text}\n
【主题】\n{search_query}"""
        report_content = llm.generate(html_prompt)
        if "<think>" in report_content:
            report_content = report_content.split("</think>")[-1].strip()
        print(f"📝 报告文案提取成功：\n{report_content}")

        customer_name = "VIP客户"
        file_path = generate_html_from_rag(report_content, customer_name)
        file_name = os.path.basename(file_path)
        download_url = f"http://127.0.0.1:8000/reports/{file_name}"
        return {
            "code": 200,
            "answer": f"✅ 已经为您生成了精美的网页版营养报告！\n\n👉 [点击这里查看/导出PDF]({download_url})",
            "source": "HTML Generator",
            "references": [],
            "contexts": []
        }

    # ================= 2. MySQL FAQ 前置拦截 =================
    faq_answer = mysql_db.search_faq(query)
    if faq_answer:
        return {"code": 200, "answer": faq_answer, "source": "MySQL FAQ 缓存",
                "references": [], "contexts": []}

    # ================= 3. 边界/闲聊兜底 =================
    if _is_edge_query(query):
        print("🛡️ 命中边界关键词，走兜底话术")
        return {"code": 200, "answer": EDGE_REPLY, "source": "Edge Guard",
                "references": [], "contexts": []}

    # ================= 4. BERT 意图识别路由 =================
    intent = router.classify_intent(query)
    if intent == "chitchat":
        chain = chitchat_prompt_template | (lambda x: llm.generate(x.to_string())) | StrOutputParser()
        answer = chain.invoke({"query": query})
        return {"code": 200, "answer": answer, "source": "LLM (Chitchat)",
                "references": [], "contexts": []}

    # ================= 5. RAG 专业检索 =================
    # [注] query 改写已关闭以降低延迟，如需启用可在此处加改写逻辑
    search_query = query
    print(f"🔎 检索用 query: {search_query}")
    query_vector = embedder.get_embedding(search_query)
    contexts = db.search(query_vector, limit=5)

    safe_texts = []
    for c in contexts:
        text = c.get("text", "")
        if len(text) > 2000:
            text = text[:2000] + "...[单块截断]"
        safe_texts.append(text)
    context_text = "\n\n---\n\n".join(safe_texts)
    if len(context_text) > 5000:
        context_text = context_text[:5000] + "\n\n...[截断]"

    references = []
    for c in contexts:
        ref_str = f"{c.get('source', '未知文件')} - {c.get('page', '未知章节')}"
        if ref_str not in references:
            references.append(ref_str)

    rag_chain = rag_prompt_template | (lambda x: llm.generate(x.to_string())) | StrOutputParser()
    answer = rag_chain.invoke({"context": context_text, "query": query})

    # ★ 关键：返回 contexts 供评测统计召回率
    return {
        "code": 200,
        "answer": answer,
        "source": "RAG",
        "references": references,
        "contexts": safe_texts,   # ← 新增，解决召回率 0%
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)