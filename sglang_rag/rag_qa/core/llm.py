from openai import OpenAI
from base.config import config

class SGLangClient:
    def __init__(self, base_url=None):
        self.client = OpenAI(base_url=base_url or config.LLM_BASE_URL, api_key="sglang")

    # 注意这里的方法名，必须叫 generate
    def generate(self, prompt):
        response = self.client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            timeout=30,
            max_tokens=512
        )
        content = response.choices[0].message.content
        if "</think>" in content:
            content = content.split("</think>")[-1].strip()
        return content