import os
import markdown
from base.config import config


def generate_html_from_rag(answer_text, customer_name):
    output_dir = os.path.join(config.PROJECT_ROOT, "output_htmls")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 核心：使用 markdown 库将文本转为漂亮的 HTML（支持列表、加粗、标题）
    html_body = markdown.markdown(answer_text, extensions=['extra'])

    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>{customer_name} 的营养方案</title>
        <style>
            body {{
                font-family: 'Helvetica Neue', Helvetica, Arial, 'Microsoft YaHei', sans-serif;
                background-color: #f4f6f8;
                color: #333;
                line-height: 1.8;
                padding: 40px;
                display: flex;
                justify-content: center;
            }}
            .report-card {{
                background: #ffffff;
                width: 100%;
                max-width: 800px;
                border-radius: 8px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.08);
                padding: 50px 60px;
                border-top: 6px solid #10a37f;
            }}
            .header {{
                border-bottom: 2px solid #eaeaea;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            .header h1 {{
                color: #10a37f;
                font-size: 32px;
                margin: 0 0 10px 0;
                letter-spacing: 1px;
            }}
            .header p {{
                color: #888;
                font-size: 14px;
                margin: 0;
            }}
            .content {{
                font-size: 16px;
                color: #2c3e50;
            }}
            /* 美化 Markdown 渲染后的标签 */
            .content h3 {{
                color: #10a37f;
                border-left: 4px solid #10a37f;
                padding-left: 10px;
                margin-top: 30px;
                font-size: 20px;
            }}
            .content ul, .content ol {{
                padding-left: 20px;
            }}
            .content li {{
                margin-bottom: 10px;
            }}
            .content strong {{
                color: #e74c3c; /* 重点词汇标红 */
            }}
            .footer {{
                margin-top: 50px;
                padding-top: 20px;
                border-top: 1px solid #eaeaea;
                font-size: 12px;
                color: #999;
                text-align: center;
            }}
            @media print {{
                body {{ background: white; padding: 0; }}
                .report-card {{ box-shadow: none; padding: 0; border-top: none; }}
            }}
        </style>
    </head>
    <body>
        <div class="report-card">
            <div class="header">
                <h1>专属营养健康方案</h1>
                <p>定制客户：{customer_name} | 由 AI Copilot 自动生成</p>
            </div>
            <div class="content">
                {html_body}
            </div>
            <div class="footer">
                本报告由大语言模型基于专业知识库自动生成，仅供参考，具体干预方案请遵医嘱。
            </div>
        </div>
    </body>
    </html>
    """

    safe_name = "".join([c for c in customer_name if c.isalnum()])
    file_name = f"{safe_name}_营养报告.html"
    file_path = os.path.join(output_dir, file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return file_path