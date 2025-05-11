# backend/main.py
from fastapi import FastAPI, Request, Form
from fastapi.responses import JSONResponse,FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uuid
from markdown import markdown
from .answer  import generate_answer_with_history, get_rag_context, get_kg_context, merge_questions
from backend.config.memory import SessionManager

app = FastAPI()
session_manager = SessionManager()

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

@app.get("/init_session")
async def init_session():
    session_id = str(uuid.uuid4())
    session_manager.create_session(session_id)
    return {"session_id": session_id}

@app.get("/")
async def index():
    return FileResponse("frontend/static/index.html")


@app.post("/ask")
async def ask(question: str = Form(...), session_id: str = Form(...)):

    history = session_manager.get_history(session_id)
    if history is not None:
        #将历史中的用户问题与当前问题合并，作为当前检索查询
        query=merge_questions(history, question)
    else:
        query=question
    
    
    print('原始问题：', question)
    print('重新构建的问题：', query)
    # 获取 RAG 和 KG 上下文
    print("正在获取 RAG 上下文...")
    rag_context = get_rag_context(query)
    print("获取 RAG 上下文完成，共获取到以下 {} 个片段。", len(rag_context))
    for i, passage in enumerate(rag_context):
        print(f"【{i+1}】{passage}")
    
    print("正在获取 KG 上下文...")
    kg_context = get_kg_context(query)
    print("获取 KG 上下文完成，共获取到以下 {} 个片段。", len(kg_context))
    for i, passage in enumerate(kg_context):
        print(f"【{i+1}】{passage}")

    # merged_context = merge_and_rerank(query, rag_context, kg_context)
    merged_context = rag_context + kg_context
    
    response = generate_answer_with_history(question, merged_context,history)
    
    answer = ""
    for chunk in response:
        answer = answer + (chunk.choices[0].delta.content or "")
        if chunk.choices[0].finish_reason == "stop":
            break
    
    print("【回答】", answer)
    session_manager.add_message(session_id, question, answer)
    answer = markdown(answer)
    
    return JSONResponse(content={
        "session_id": session_id,
        "history": session_manager.get_full_history(session_id),
        "question": question,
        "answer": answer,
        "rag_context": rag_context,
        "kg_context": kg_context,
    })