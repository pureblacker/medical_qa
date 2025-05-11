from typing import Callable, List, Dict, Tuple
from langchain_core.documents import Document
from backend.LLM.LLMclientgeneric import LLMclientgeneric
from backend.search.retrieve_model import Retrieve_model


def format_docs(docs:List[Document]):
    return "\n-------------分割线--------------\n".join(doc.page_content for doc in docs)


def retrieve_docs(question:str)->Tuple[List[Document],str]:
    retriever= Retrieve_model()._retriever
    docs = retriever.invoke(question)
    _context = format_docs(docs) # 这里处理成文本
    # print(_context)
    return (docs,_context)


# def RAG_tool(

#     question: str,
#     history: List[List | None] = None,
#     image_url=None,
# ):
#     # 先利用question去检索得到docs
#     try:
#         docs, _context = retrieve_docs(question)  # 此处得到的是检索到的文件片段和文件处理后的文本
#     except Exception as e:
#         _context = ""

#     prompt = f"请根据搜索到的文件信息\n{_context}\n 回答问题：\n{question}"
#     response = LLMclientgeneric().chat_with_ai_stream(prompt)
#     return response


# if __name__ == "__main__":
#     RAG_tool("头痛眼花")