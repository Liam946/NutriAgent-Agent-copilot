from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from base.config import config
from rag_qa.core.embedding import BGEEmbedding
from rag_qa.core.milvus_db import MilvusDB
from rag_qa.core.llm import SGLangClient
from rag_qa.core.mysql_db import MySQLDB
from base.router import IntentRouter

# 引入 HTML 生成工具
from rag_qa.tools.html_generator import generate_html_from_rag

app = FastAPI(title="营养健康 Copilot API (LangChain版)")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"],
                   allow_headers=["*"])

# ================= 挂载静态文件目录 =================
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

# (LangChain 模板保持不变)
rag_prompt_template = ChatPromptTemplate.from_messages([
    ("system", "你是一个专业的营养师。请认真阅读以下参考资料，然后回答用户的问题。\n\n【参考资料】\n{context}"),
    ("human",
     "{query}\n\n【回答要求】\n1. 如果参考资料中提到了相关内容，请提取出来并总结。\n2. 严禁直接回答“资料不足”。\n3. 请分点作答，保持专业。")
])
chitchat_prompt_template = ChatPromptTemplate.from_messages([
    ("system", "你是一个友好的营养健康助手。请简短、礼貌地回答用户。"),
    ("human", "{query}")
])


class ChatRequest(BaseModel):
    query: str


@app.post("/api/chat")
async def chat(request: ChatRequest):
    query = request.query
    print(f"\n👤 用户 Query: {query}")

    # ================= 1. 拦截并处理 报告生成 意图 =================
    if "生成报告" in query or "生成PPT" in query or "做方案" in query:
        print("📊 识别到生成报告意图，正在调用 RAG 提取大纲...")

        search_query = query.replace("生成PPT", "").replace("做个ppt", "").replace("帮我", "").replace("生成报告", "").strip()
        if not search_query:
            search_query = "高血压患者的一日三餐建议"

        query_vector = embedder.get_embedding(search_query)
        contexts = db.search(query_vector, limit=3)
        context_text = "\n\n".join([c.get("text", "") for c in contexts])

        # 让大模型输出极其规范的 Markdown 格式
        html_prompt = f"""请根据以下资料，提取核心内容，生成一份结构清晰的营养报告。
要求：
1. 必须包含“一、核心建议”和“二、注意事项”两个模块。
2. 使用 Markdown 格式，使用短句，多使用加粗（**重点**）和无序列表（- 列表项）。
3. 字数控制在300字左右，适合在网页上阅读。

【资料】\n{context_text}\n
【主题】\n{search_query}"""

        report_content = llm.generate(html_prompt)

        # 清洗掉 0.6B 模型的 think 标签
        if "<think>" in report_content:
            report_content = report_content.split("</think>")[-1].strip()

        print(f"📝 报告文案提取成功：\n{report_content}")

        # 调用工具生成精美的 HTML 报告
        customer_name = "VIP客户"
        file_path = generate_html_from_rag(report_content, customer_name)
        file_name = os.path.basename(file_path)

        download_url = f"http://127.0.0.1:8000/reports/{file_name}"
        return {
            "code": 200,
            "answer": f"✅ 已经为您生成了精美的网页版营养报告！\n\n👉 [点击这里查看/导出PDF]({download_url})",
            "source": "HTML Generator",
            "references": []
        }

    # ================= 2. MySQL FAQ 前置拦截 =================
    faq_answer = mysql_db.search_faq(query)
    if faq_answer:
        return {"code": 200, "answer": faq_answer, "source": "MySQL FAQ 缓存", "references": []}

    # ================= 3. BERT 意图识别路由 =================
    intent = router.classify_intent(query)

    if intent == "chitchat":
        chain = chitchat_prompt_template | (lambda x: llm.generate(x.to_string())) | StrOutputParser()
        answer = chain.invoke({"query": query})
        return {"code": 200, "answer": answer, "source": "LLM (Chitchat)", "references": []}

    # ================= 4. RAG 专业检索 =================
    query_vector = embedder.get_embedding(query)
    contexts = db.search(query_vector, limit=5)

    # 截断逻辑，防止超长文本撑爆大模型
    safe_texts = []
    for c in contexts:
        text = c.get("text", "")
        if len(text) > 2000:
            text = text[:2000] + "...[单块截断]"
        safe_texts.append(text)
    context_text = "\n\n---\n\n".join(safe_texts)
    if len(context_text) > 5000:
        context_text = context_text[:5000] + "\n\n...[截断]"

    # 提取引用来源
    references = []
    for c in contexts:
        ref_str = f"{c.get('source', '未知文件')} - {c.get('page', '未知章节')}"
        if ref_str not in references:
            references.append(ref_str)

    # 生成回答
    rag_chain = rag_prompt_template | (lambda x: llm.generate(x.to_string())) | StrOutputParser()
    answer = rag_chain.invoke({"context": context_text, "query": query})

    return {"code": 200, "answer": answer, "source": "RAG", "references": references}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)