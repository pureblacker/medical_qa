'''本地知识库的RAG检索模型类'''
import os
import gc
import shutil
import backend.model.Embedding as Embedding
from backend.config.config import load_nested_params
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_community.document_loaders import (
    DirectoryLoader,
    PyPDFLoader,
    MHTMLLoader,
    TextLoader,
    CSVLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader,
)

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.faiss import FAISS


import re
from typing import Generator

class OptimizedCleaner:
    # 预编译所有正则（只需一次）
    _regex = {
        # 1. 移除所有空白符（含换行、制表符、零宽空格等）
        'normalize_whitespace': re.compile(r'[\s\u200B\u200C\u200D\uFEFF]+', re.UNICODE),
        # 2. 移除ASCII控制字符（含DEL）
        'remove_ascii_controls': re.compile(r'[\x00-\x1F\x7F-\x9F]', re.UNICODE),
        # 3. 移除Unicode私有区字符（U+E000-U+F8FF）
        'remove_private_use': re.compile(r'[\uE000-\uF8FF]', re.UNICODE),
        # 4. 移除常见特殊符号（可按需扩展）
        'remove_symbols': re.compile(r'[\u2022\u2192\u25A0\u25CF\u25CB]', re.UNICODE),
        # 5. 合并连续空格为单个空格
        'compact_spaces': re.compile(r' {2,}'),
        # 6. 移除重复的特殊符号（如连续*、_等）
        'remove_repeated_symbols': re.compile(r'([^\w\s])\1{2,}'),
        # 7. 移除目录占位符（连续点号）
        'remove_toc_placeholders': re.compile(r'\.{3,}|\s+\.\s+'),
        # 8. 移除重复标点符号
        'remove_repeated_punctuations': re.compile(r'([. .,!?;:])')
    }

    @classmethod
    def process_stream(cls, document_stream: Generator) -> Generator:
        """流式处理文档"""
        for doc in document_stream:
            text = doc.page_content
            
            # 按顺序清洗
            text = cls._regex['normalize_whitespace'].sub(' ', text)        # 归一化空白符
            text = cls._regex['remove_ascii_controls'].sub('', text)        # 移除ASCII控制字符
            text = cls._regex['remove_private_use'].sub('', text)          # 移除私有区字符
            text = cls._regex['remove_symbols'].sub('', text)              # 移除特殊符号
            text = cls._regex['remove_repeated_symbols'].sub(r'\1', text)  # 移除重复符号
            text = cls._regex['compact_spaces'].sub(' ', text)             # 合并空格
            text = cls._regex['remove_toc_placeholders'].sub(' ', text) # 移除目录占位符（连续点号）
            text = cls._regex['remove_repeated_punctuations'].sub(r'\1', text) # 移除重复标点符号
            # 去除首尾空白
            text = text.strip()
            
            # 仅保留非空文档
            if text:
                doc.page_content = text
                yield doc



# 检索模型
class Retrieve_model(object):

    _retriever: VectorStoreRetriever

    def __init__(self):
        super().__init__()
        
        self.embedding_model = Embedding.LoadModel()

        self.knowledge_path = load_nested_params("knowledge-path")
        if not os.path.exists(self.knowledge_path):
            os.makedirs(self.knowledge_path)
        
        self.faiss_path = load_nested_params("faiss-path")
        
        #检查self.faiss_path文件夹是否为空
        if not os.listdir(self.faiss_path):
            print(f"{self.faiss_path}文件夹为空")
            self.build_vectorstore()
        
        # 加载向量库
        self.vectorstore = FAISS.load_local(self.faiss_path, embeddings=self.embedding_model,allow_dangerous_deserialization=True)
        print("加载向量库成功")
        # 将向量存储转换为检索器，设置检索参数 k 为 6，即返回最相似的 6 个文档
        self._retriever = self.vectorstore.as_retriever(search_kwargs={"k": 6})
    
    # 加载文件
    def load_file(self,file_path):

        # 加载PDF文件
        pdf_loader = DirectoryLoader(
            file_path,
            glob="**/*.pdf",
            loader_cls=PyPDFLoader,
            silent_errors=True,
            use_multithreading=True,
        )
        pdf_docs = pdf_loader.load()

        # 加载Word文件
        docx_loader = DirectoryLoader(
            file_path,
            glob="**/*.docx",
            loader_cls=UnstructuredWordDocumentLoader,
            silent_errors=True,
            use_multithreading=True,
        )
        docx_docs = docx_loader.load()

        # 加载txt文件
        txt_loader = DirectoryLoader(
            file_path,
            glob="**/*.txt",
            loader_cls=TextLoader,
            silent_errors=True,
            loader_kwargs={"autodetect_encoding": True},
            use_multithreading=True,
        )
        txt_docs = txt_loader.load()

        # 加载csv文件
        csv_loader = DirectoryLoader(
            file_path,
            glob="**/*.csv",
            loader_cls=CSVLoader,
            silent_errors=True,
            loader_kwargs={"autodetect_encoding": True},
            use_multithreading=True,
        )
        csv_docs = csv_loader.load()

        # 加载html文件
        html_loader = DirectoryLoader(
            file_path,
            glob="**/*.html",
            loader_cls=UnstructuredHTMLLoader,
            silent_errors=True,
            use_multithreading=True,
        )
        html_docs = html_loader.load()

        mhtml_loader = DirectoryLoader(
            file_path,
            glob="**/*.mhtml",
            loader_cls=MHTMLLoader,
            silent_errors=True,
            use_multithreading=True,
        )
        mhtml_docs = mhtml_loader.load()

        # 加载markdown文件
        markdown_loader = DirectoryLoader(
            file_path,
            glob="**/*.md",
            loader_cls=UnstructuredMarkdownLoader,
            silent_errors=True,
            use_multithreading=True,
        )
        markdown_docs = markdown_loader.load()
        
        print(f"加载文档完成，共加载了{len(pdf_docs)}个pdf文档,{len(docx_docs)}个docx文档, {len(txt_docs)}个txt文档, {len(csv_docs)}个csv文档, {len(html_docs)}个html文档, {len(mhtml_docs)}个mhtml文档, {len(markdown_docs)}个markdown文档")
        # 合并文档
        docs = (
            pdf_docs
            + docx_docs
            + txt_docs
            + csv_docs
            + html_docs
            + mhtml_docs
            + markdown_docs
        )
        # 清洗文档
        docs = list(OptimizedCleaner.process_stream(docs))

        # 分割文档,使其按句号分割
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", ".", "!", "?", "。", "！", "？"],
            chunk_size=500, chunk_overlap=100
        )
        splits = text_splitter.split_documents(docs)
        print(f"分割文档完成，共分割了{len(splits)}个块")

        for i, doc in enumerate(splits[:3]):
            print(f"文档 {i}:\n{doc.page_content[:200]}\n")

        return splits


    # 创建向量库
    def build_vectorstore(self,):
        
        splits=self.load_file(self.knowledge_path)
        
        try:
            vectorstore = None
            batch_size = 10  
            faiss_temp_path = self.faiss_path + "_temp"  # 临时保存路径

            for i in range(0, len(splits), batch_size):
                batch = splits[i:i+batch_size]
                
                # 如果是第一个批次，创建新向量库并保存
                if i == 0:
                    vectorstore = FAISS.from_documents(documents=batch, embedding=self.embedding_model)
                    vectorstore.save_local(faiss_temp_path)
                    print(f"初始批次已保存至临时路径: {faiss_temp_path}")
                    
                # 后续批次：加载已有库 -> 添加新数据 -> 覆盖保存
                else:
                    vectorstore = FAISS.load_local(
                        faiss_temp_path,
                        embeddings=self.embedding_model,
                        allow_dangerous_deserialization=True  # 允许加载不安全的序列化对象
                    )  
                    
                    vectorstore.add_documents(batch)  # 添加新文档
                    vectorstore.save_local(faiss_temp_path) # 覆盖保存更新后的库
                    print(f"增量保存第 {i//batch_size} 批数据")
                
                # 手动释放内存
                del vectorstore
                gc.collect()
                print(f"已处理 {min(i + batch_size, len(splits))} 个文档块 (共 {len(splits)})")

            # 全部完成后重命名为正式路径
            if os.path.exists(faiss_temp_path):
                os.rename(faiss_temp_path, self.faiss_path)
                print(f"向量数据库最终保存至: {self.faiss_path}")

        except Exception as e:
            print(f"处理过程中发生错误: {e}")
            # 清理可能的残留临时文件
            if os.path.exists(faiss_temp_path):
                shutil.rmtree(faiss_temp_path)
            raise

# if __name__ == '__main__':
#     retrieve_model=Retrieve_model()
#     retrieve_model._retriever.invoke('头痛眼花')