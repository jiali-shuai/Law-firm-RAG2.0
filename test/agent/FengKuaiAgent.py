from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from typing import List

from load.load_word import load_word_document_file
from load.load_pdf import load_pdf_document_file


"""语义分块 Agent - BGE-M3语义相似度 + 动态百分位法 + LLM灰色地带"""
class SmartChunkerAgent:

    def __init__(self, chat_llm: ChatOpenAI):
        self.chat_llm = chat_llm

    def load_and_chunk_word(self, file_path: str, lower_percentile: int = 25, upper_percentile: int = 75) -> List[Document]:
        return load_word_document_file(
            file_path,
            chat_llm=self.chat_llm,
            lower_percentile=lower_percentile,
            upper_percentile=upper_percentile,
        )

    def load_and_chunk_pdf(self, file_path: str, lower_percentile: int = 25, upper_percentile: int = 75) -> List[Document]:
        return load_pdf_document_file(
            file_path,
            chat_llm=self.chat_llm,
            lower_percentile=lower_percentile,
            upper_percentile=upper_percentile,
        )




# """智能分块 Agent - 加载整个文档，让LLM根据内容智能分块"""
   
    
#     def load_and_chunk_word(self, file_path: str) -> List[Document]:
#         """加载Word文档，让LLM根据内容智能分块"""
    
#         abs_path = os.path.abspath(file_path)
#         doc = docx.Document(abs_path)
#         texts = []
#         for para in doc.paragraphs:
#             if para.text.strip():
#                 texts.append(para.text)

#         full_text = "\n".join(texts)
#         return full_text


# def llm_chunk_full_text(self, full_text: str) -> List[Document]:
#         print("智能分块 Agent 启动...")

#         respose = self.chat_llm.invoke([
#             ("system", self.chunking_prompt),
#             ("user", full_text)
#         ])

#         response = json.loads(respose.content)
#         chunks_data = response["chunks"]

#         chunked_docs = []
#         for chunk_info in chunks_data:
#             doc = Document(
#                 page_content=chunk_info.get("content", ""),
#                 metadata={}
#             )
#             chunked_docs.append(doc)

#         print(f"智能分块完成，共 {len(chunked_docs)} 个chunk")
#         return chunked_docs
