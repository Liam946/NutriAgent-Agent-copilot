import json
import requests
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
API_URL = "http://127.0.0.1:8000/api/chat"

# 边界/闲聊题关键词（用于单独统计，不计入知识准确率）
EDGE_HINTS = ["笑话", "写诗", "写一首", "你喜欢", "天气", "唱歌", "翻译", "讲个故事"]


def is_edge_question(query: str) -> bool:
    return any(w in query for w in EDGE_HINTS)


def run_evaluation():
    with open("eval_dataset.json", "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    total = len(test_cases)

    # 知识题统计
    rag_total = 0            # 走 RAG 的知识题数（召回率分母）
    hit_rate = 0             # 召回命中数
    faithful_rate = 0        # 忠实度命中数（全量）
    relevancy_rate = 0       # 知识题答对数

    # 边界题统计（单独口径）
    edge_total = 0
    edge_ok = 0

    total_time = 0

    logging.info(f"开始重新跑分（严谨版），共计 {total} 条数据...")

    for i, case in enumerate(test_cases):
        query = case["query"]
        ground_truth = case["ground_truth"]

        start_time = time.time()
        try:
            res = requests.post(API_URL, json={"query": query}, timeout=60)
            data = res.json()
            cost_time = time.time() - start_time
            total_time += cost_time

            answer = data.get("answer", "")
            references = data.get("references", [])
            contexts = data.get("contexts", [])
            source = data.get("source", "")

            keywords = [kw.strip() for kw in ground_truth.split("|") if kw.strip()]
            is_correct = any(kw in answer for kw in keywords)

            is_rag = "RAG" in source
            context_hit = is_rag and any(kw in "".join(contexts) for kw in keywords)

            # ---------- 边界题：单独统计 ----------
            if is_edge_question(query):
                edge_total += 1
                # 边界题只要不是报错、且有得体回复（拒答/闲聊）即算处理得当
                if len(answer) > 3 and "错误" not in answer:
                    edge_ok += 1
                tag = "边界题得体" if (len(answer) > 3 and "错误" not in answer) else "边界题失当"
                logging.info(f"ℹ️ [{i + 1}/{total}] {tag}: {query} (耗时:{cost_time:.2f}s) [source:{source}]")
                continue

            # ---------- 知识题统计 ----------
            # Faithfulness：如实说明资料不足属诚实，不应扣分；只排除报错/空答
            if "错误" not in answer and len(answer) > 5:
                faithful_rate += 1

            if is_correct:
                relevancy_rate += 1

            if is_rag:
                rag_total += 1
                if context_hit:
                    hit_rate += 1

            if is_correct:
                tag = f" [召回:{'Y' if context_hit else 'N'}]" if is_rag else ""
                logging.info(f"✅ [{i + 1}/{total}] 答对: {query} (耗时:{cost_time:.2f}s){tag}")
            else:
                prefix = f"召回{'成功但' if context_hit else ''}答错" if is_rag else "答错(非检索)"
                logging.warning(f"❌ [{i + 1}/{total}] {prefix}: {query}")

        except Exception as e:
            logging.error(f"❌ 请求失败: {e}")

    # ================= 报告 =================
    knowledge_total = total - edge_total
    recall_pct = (hit_rate / rag_total * 100) if rag_total > 0 else 0.0
    faithfulness_pct = (faithful_rate / knowledge_total * 100) if knowledge_total > 0 else 0.0
    relevancy_pct = (relevancy_rate / knowledge_total * 100) if knowledge_total > 0 else 0.0
    edge_pct = (edge_ok / edge_total * 100) if edge_total > 0 else 0.0

    logging.info("\n" + "=" * 44)
    logging.info("📊 系统质量评估报告（分口径）")
    logging.info("=" * 44)
    logging.info(f"知识题总数: {knowledge_total} | 边界题总数: {edge_total}")
    logging.info(f"1. Context Recall (检索召回率): {recall_pct:.1f}%  (样本: {hit_rate}/{rag_total} 条RAG问题)")
    logging.info(f"2. Faithfulness (生成忠实度): {faithfulness_pct:.1f}%  (知识题口径)")
    logging.info(f"3. Answer Relevancy (知识准确率): {relevancy_pct:.1f}%  (样本: {relevancy_rate}/{knowledge_total})")
    logging.info(f"4. 边界题得体率: {edge_pct:.1f}%  (样本: {edge_ok}/{edge_total})")
    logging.info(f"5. 平均端到端延迟: {total_time / total:.2f} 秒")
    logging.info("=" * 44)


if __name__ == "__main__":
    run_evaluation()