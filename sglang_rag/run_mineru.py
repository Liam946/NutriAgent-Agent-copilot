import os
import subprocess

# 你的 PDF 绝对路径
pdf_path_1 = r"E:\workspace\EduRAG\SGLangRAG\sglang_rag\rag_qa\data\中国居民膳食指南2022.pdf"
pdf_path_2 = r"E:\workspace\EduRAG\SGLangRAG\sglang_rag\rag_qa\data\中国高血压防治指南(2024年修订版).pdf"

# 定义输出的 Markdown 文件路径（直接输出到项目根目录，方便后面读取）
output_md_1 = r"E:\workspace\EduRAG\SGLangRAG\sglang_rag\膳食指南.md"
output_md_2 = r"E:\workspace\EduRAG\SGLangRAG\sglang_rag\高血压.md"

def run_mineru(pdf_path, output_path):
    print(f"🚀 正在使用 MinerU 解析: {os.path.basename(pdf_path)}")
    # 调用 MinerU 的命令行工具
    cmd = [
        "mineru-kit", "parse", pdf_path,
        "-o", output_path,
        "--tier", "standard"
    ]
    try:
        # 运行命令并实时打印输出
        subprocess.run(cmd, check=True)
        print(f"✅ 解析成功，输出文件: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ 解析失败: {e}")
        print("💡 提示：请确保 Docker 里的 SGLang 已经停止 (docker stop sglang-server)，否则可能显存不足。")

if __name__ == "__main__":
    # 注意：跑之前先停掉大模型，防止显存冲突
    run_mineru(pdf_path_1, output_md_1)
    run_mineru(pdf_path_2, output_md_2)