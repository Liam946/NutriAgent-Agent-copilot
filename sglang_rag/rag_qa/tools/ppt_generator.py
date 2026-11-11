import os
import re
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from base.config import config


def generate_ppt_from_rag(answer_text, customer_name):
    output_dir = os.path.join(config.PROJECT_ROOT, "output_ppts")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    prs = Presentation()

    # 定义主题色（与前端一致的绿色）
    THEME_COLOR = RGBColor(16, 163, 127)
    TEXT_COLOR = RGBColor(51, 51, 51)

    # ================= 1. 封面页 =================
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    title = slide.shapes.title
    subtitle = slide.placeholders[1]

    title.text = "专属营养健康方案"
    title.text_frame.paragraphs[0].font.size = Pt(44)
    title.text_frame.paragraphs[0].font.bold = True
    title.text_frame.paragraphs[0].font.color.rgb = THEME_COLOR

    subtitle.text = f"定制客户：{customer_name}\n\n由 AI Copilot 自动生成"
    subtitle.text_frame.paragraphs[0].font.size = Pt(20)
    subtitle.text_frame.paragraphs[0].font.color.rgb = TEXT_COLOR

    # ================= 2. 正文页（自动分页排版） =================
    # 将大模型输出的长文本，按句号、换行符拆解成短句
    sentences = re.split(r'[。\n]', answer_text)
    # 过滤掉太短的废话（比如“建议”、“总结”等）
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]

    if not sentences:
        sentences = ["暂无详细建议，请参考专业指南。"]

    # 每页最多展示 4 条，防止文字溢出屏幕
    items_per_slide = 4
    for i in range(0, len(sentences), items_per_slide):
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        title = slide.shapes.title
        title.text = "核心膳食建议"
        title.text_frame.paragraphs[0].font.color.rgb = THEME_COLOR
        title.text_frame.paragraphs[0].font.bold = True

        content = slide.placeholders[1]
        tf = content.text_frame

        current_batch = sentences[i:i + items_per_slide]
        for idx, sentence in enumerate(current_batch):
            if idx == 0:
                p = tf.paragraphs[0]
            else:
                p = tf.add_paragraph()

            # 增加序号和圆点，提升专业感
            p.text = f"{i + idx + 1}. {sentence}"
            p.font.size = Pt(20)
            p.font.color.rgb = TEXT_COLOR
            p.space_after = Pt(20)  # 增加行距

    # ================= 3. 保存 =================
    safe_customer_name = "".join([c for c in customer_name if c.isalnum() or c in (' ', '_', '-')]).strip()
    if not safe_customer_name:
        safe_customer_name = "未命名客户"

    file_name = f"{safe_customer_name}_营养方案.pptx"
    file_path = os.path.join(output_dir, file_name)
    prs.save(file_path)

    return file_path