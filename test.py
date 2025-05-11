import os
from search.rag_search_tool import retrieve_docs
from search.kg_search_tool import check_entity, relation_tool
from client.LLMclientgeneric import LLMclientgeneric
from model.Rerank import Reranker  
from langchain.memory import ConversationBufferMemory

# 初始化组件
# reranker = Reranker()
memory = ConversationBufferMemory()
llm_client = LLMclientgeneric()


def get_rag_context(question):
    docs, context = retrieve_docs(question)
    return context.split('\n-------------分割线--------------\n')

def get_kg_context(question):
    entities = check_entity(question)
    kg_info = relation_tool(entities)
    return kg_info.split('；')


def merge_and_rerank(query, rag_passages, kg_passages):
    all_passages = rag_passages + kg_passages
    top_5 = reranker.rerank(query, all_passages, 5)
    return top_5


def generate_answer_with_history(query, context_list):
    # 获取历史对话记录（格式为 List[List[str]]）
    history = memory.load_memory_variables({}).get("history", [])

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




def main():
    print("欢迎使用智能问答系统，输入 'exit' 退出。")

    while True:
        user_input = input("User: ").strip()
        if user_input.lower() == "exit":
            print("再见！")
            break

        # 获取 RAG 和 KG 上下文
        print("正在获取 RAG 上下文...")
        rag_context = get_rag_context(user_input)
        print("获取 RAG 上下文完成，共获取到以下 {} 个片段。", len(rag_context))
        for i, passage in enumerate(rag_context):
            print(f"【{i+1}】{passage}")
        
        print("正在获取 KG 上下文...")
        kg_context = get_kg_context(user_input)
        print("获取 KG 上下文完成，共获取到以下 {} 个片段。", len(kg_context))
        for i, passage in enumerate(kg_context):
            print(f"【{i+1}】{passage}")

        # 合并并重排
        # merged_context = merge_and_rerank(user_input, rag_context, kg_context)
        merged_context = rag_context + kg_context
        
        # 生成回答
        response = generate_answer_with_history(user_input, merged_context)

        bot_response = ""
        for chunk in response:
            bot_response = bot_response + (chunk.choices[0].delta.content or "")
            if chunk.choices[0].finish_reason == "stop":
                break
        
        # 打印回答并更新记忆
        print(f"AI: {bot_response}")
        memory.save_context({"input": user_input}, {"output": bot_response})

if __name__ == "__main__":
    main()