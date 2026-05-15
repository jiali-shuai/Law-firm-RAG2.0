"""加载PDF文档并智能分块"""

import fitz
import os

from load.smart_chunker import smart_chunk_texts


def load_pdf_document_file(file_path, chat_llm=None, lower_percentile=25, upper_percentile=75):
    abs_path = os.path.abspath(file_path)
    doc = fitz.open(abs_path)
    texts = []
    for page in doc:
        page_text = page.get_text("text").strip()
        if page_text:
            blocks = page.get_text("blocks")
            for block in blocks:
                block_text = block[4].strip()
                if block_text:
                    texts.append(block_text)
    doc.close()

    print(f"成功加载PDF文档，共解析出 {len(texts)} 个文本块")
    return smart_chunk_texts(texts, chat_llm=chat_llm, lower_percentile=lower_percentile, upper_percentile=upper_percentile)
