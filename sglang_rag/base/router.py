import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from base.config import config
import os


class IntentRouter:
    def __init__(self):
        # 我们加载你本地已有的 bert-base-chinese 模型文件夹
        # 注意：这里我们没有真正微调过，只是为了跑通流程，直接初始化一个二分类头（2个标签：0=通用，1=专业）
        self.model_path = os.path.join(config.MODELS_DIR, "bert-base-chinese")
        print(f"正在加载 BERT 意图识别模型: {self.model_path}")

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            # num_labels=2 表示二分类
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_path, num_labels=2)
            self.model.eval()  # 设置为推理模式
        except Exception as e:
            print(f"⚠️ 加载模型失败，请确保 bert-base-chinese 文件夹存在。错误: {e}")

        # 为了演示，我们写死一些关键词。如果没有微调，模型是瞎猜的。
        # 真实项目里，你要用几百条数据微调它，然后删掉这个关键词规则。
        self.medical_keywords = ["高血压", "糖尿病", "维生素", "吃什么", "营养", "减肥", "孕妇", "热量"]

    def classify_intent(self, query):
        """
        返回意图类型： 'chitchat' (闲聊) 或 'professional' (专业知识)
        """
        # 策略1：如果包含专业关键词，直接判定为专业问题（工程兜底）
        for kw in self.medical_keywords:
            if kw in query:
                return "professional"

        # 策略2：调用 BERT 模型进行预测
        inputs = self.tokenizer(query, return_tensors="pt", truncation=True, max_length=64)
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.argmax(outputs.logits, dim=-1)
            label = predictions.item()

        # 假设 label 1 是专业，0 是闲聊
        if label == 1:
            return "professional"
        else:
            # 如果没命中关键词，模型也没预测出专业，就当闲聊处理
            return "chitchat"