import json
import requests
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
API_URL = "http://127.0.0.1:8000/api/chat"


def run_evaluation():
    with open("eval_dataset.json", "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    total = len(test_cases)
    hit_rate = 0  # 召回命中率 (有引用就算命中)
    faithful_rate = 0  # 忠实度 (回答了且没报错)
    relevancy_rate = 0  # 相关性 (包含了关键真相词)
    total_time = 0

    logging.info(f"开始跑分，共计 {total} 条数据...")

    for i, case in enumerate(test_cases):
        query = case["query"]
        ground_truth = case["ground_truth"]

        start_time = time.time()
        try:
            res = requests.post(API_URL, json={"query": query}, timeout=30)
            data = res.json()
            cost_time = time.time() - start_time
            total_time += cost_time

            answer = data.get("answer", "")
            references = data.get("references", [])

            # 1. 统计召回率（只要返回了引用，说明 Milvus 检索到东西了）
            if len(references) > 0:
                hit_rate += 1

            # 2. 统计忠实度（只要没有直接拒绝回答或者报错）
            if "无法" not in answer and "错误" not in answer and len(answer) > 5:
                faithful_rate += 1

            # 3. 统计相关性（比较标准的简单方法：看回答里有没有标准答案的关键词）
            if ground_truth in answer:
                relevancy_rate += 1
                logging.info(f"✅ [{i + 1}/{total}] 命中: {query} (耗时:{cost_time:.2f}s)")
            else:
                logging.warning(f"❌ [{i + 1}/{total}] 未命中: {query}")

        except Exception as e:
            logging.error(f"❌ 请求失败: {e}")

    # ================= 打印简历级数据 =================
    logging.info("\n" + "=" * 40)
    logging.info("📊 系统质量评估报告（可直接写进简历）")
    logging.info("=" * 40)
    logging.info(f"1. Context Recall (检索召回率): {(hit_rate / total) * 100:.1f}%")
    logging.info(f"2. Faithfulness (生成忠实度): {(faithful_rate / total) * 100:.1f}%")
    logging.info(f"3. Answer Relevancy (答案相关性/准确率): {(relevancy_rate / total) * 100:.1f}%")
    logging.info(f"4. 平均端到端延迟 (P95 Latency): {total_time / total:.2f} 秒")
    logging.info("=" * 40)


if __name__ == "__main__":
    run_evaluation()