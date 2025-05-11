from backend.config.memory import SessionManager
from backend.search.rag_search_tool import retrieve_docs
from backend.search.kg_search_tool import check_entity, relation_tool
from backend.model.Rerank import Reranker
from backend.LLM.LLMclientgeneric import LLMclientgeneric


# reranker = Reranker()
llm_client = LLMclientgeneric()
session_manager = SessionManager()

def get_rag_context(question):
    docs, context = retrieve_docs(question)
    return context.split('\n-------------分割线--------------\n')

def get_kg_context(question):
    entities = check_entity(question)
    kg_info = relation_tool(entities)
    if kg_info:
        return kg_info.split('；')
    else:
        return []


def merge_and_rerank(query, rag_passages, kg_passages):
    all_passages = rag_passages + kg_passages
    top_5 = reranker.rerank(query, all_passages, 5)
    return top_5

def generate_answer_with_history(query, context_list,history):

    # 构造 prompt（仅包含当前问题和检索上下文）
    formatted_context = "\n".join([f"【{i+1}】{ctx}" for i, ctx in enumerate(context_list)])
    prompt = f"""
    根据以下信息回答用户的问题：
    {formatted_context}

    问题：{query}
    """

    # 调用大模型，传入历史和当前问题
    response = llm_client.chat_with_ai_stream(prompt, history)

    return response

def merge_questions(history, question):
    q_list = '；'.join([q for q, a in history])
    prompt = f"""
    结合用户历史提问，对用户当前问题进行补充，使其更加完整：
    历史提问：{q_list}
    当前问题：{question}
    只需输出补充后的完整问题，无需其他解释。
    """
    response = llm_client.chat_with_ai(prompt)
    return response