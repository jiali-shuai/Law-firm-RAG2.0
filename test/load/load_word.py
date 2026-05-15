"""加载Word文档并智能分块"""
import docx
import os

from load.smart_chunker import smart_chunk_texts


def load_word_document_file(file_path, chat_llm=None, lower_percentile=25, upper_percentile=75):
    abs_path = os.path.abspath(file_path)
    doc = docx.Document(abs_path)
    texts = []
    for para in doc.paragraphs:
        if para.text.strip():
            texts.append(para.text)

    print(f"成功加载Word文档，共解析出 {len(texts)} 个段落")
    return smart_chunk_texts(texts, chat_llm=chat_llm, lower_percentile=lower_percentile, upper_percentile=upper_percentile)
