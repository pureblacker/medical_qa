# 医疗问答系统（MEDICAL_QA）

## 一、项目概述

本项目是一个基于 **RAG（检索增强生成）** 和 **知识图谱（KG）** 的医疗领域智能问答系统，利用大模型api+文本向量库检索+知识图谱检索实现多轮对话、实时检索和流式回答。
系统通过以下核心组件实现：

1. **双模态检索**：结合向量数据库（FAISS）和知识图谱（Neo4j）进行上下文检索；
2. **大模型集成**：支持 OpenAI、通义千问等主流大模型；
3. **会话管理**：基于内存存储的对话历史记录；
4. **Web 界面**：使用 FastAPI + ajax 实现响应式前端。

## 二、 总体流程
1. 用户输入问题；
2. 系统查询会话历史记录，通过大模型将问题与历史记录合并，形成完整查询；
3. 系统通过双模态检索获取相关上下文；
    31. 知识图谱检索：
    - 知识图谱来自http://data.openkg.cn/dataset/medicalgraph，直接下载后导入neo4j。
    - 利用pyahocorasick库实现模糊匹配，根据问题从知识图谱中检索相关实体。
    - 利用neo4j的Cypher查询语言，根据实体查询相关关系，形成上下文。
    32. 文本向量库检索：
    - 文本来自pdf文档，利用langchain框架处理分块向量化后存入faiss库。后续可以实现根据用户上传的文档，实时生成向量库进行检索。
    - langchain框架利用向量库检索器，将查询转化为向量，在faiss库中检索相似向量，形成上下文。
4. 检索到的知识图谱上下文和文本向量库上下文合并，通过重排模型进行排序，返回前5个上下文；
4. 将重排后的上下文在prompt中作为背景知识，通过大模型生成答案；
5. 系统将答案返回给用户，并更新会话历史记录。

---

## 三、项目结构

```
MEDICAL_QA/
├── backend/                # 后端服务
│   ├── config/             # 配置模块
│   │   ├── config-web.yaml # 系统配置信息，包含检索模型、知识库、向量库地址、neo4j连接信息
│   │   ├── config.py       # 加载配置文件中的参数
│   │   └── memory.py       # 会话状态管理，用于存储对话历史
│   ├── faiss_index/        # FAISS 向量索引数据，存储知识库数据中的文本向量
│   ├── knowledges/         # 知识库数据，
│   ├── LLM/                # 大模型客户端
│   │   ├── LLMclientbase.py # 抽象基类，读取配置文件定义大模型客户端
│   │   └── LLMclientgeneric.py # 具体实现大模型流式回答等功能
│   ├── model/              # 检索模型相关
│   │   ├── bge-large-zh-v1.5 # 向量嵌入模型
│   │   ├── bge-reranker-v2-m3 # 重排模型
│   │   ├── Embedding.py    # 调用向量嵌入模型
│   │   └── Rerank.py       # 调用重排模型，对检索结果进行排序，返回前5个结果
│   ├── search/             # 检索模块
│   │   ├── kg_search_service.py # 实现知识图谱检索关键代码，获取与问题相关的实体
│   │   ├── kg_search_tool.py # 根据相关实体获取关系
│   │   ├── rag_search_tool.py # RAG 检索工具
│   │   └── retrieve_model.py # 定义向量库检索模型，实现对知识库的切分、向量化、存入向量库
│   ├── answer.py           # 回答生成逻辑，调用大模型根据双模态检索结果生成回答
│   ├── Graph.py            # 连接图数据库，查询实体关系
│   └── main.py             # 主程序入口
├── frontend/               # 前端页面
│   ├── static/             # 静态资源
│   │   ├── index.html      # HTML 模板
│   │   ├── main.js         # JavaScript 交互
│   │   └── style.css       # 样式表
├── .env                    # 环境变量配置，包含大模型API 密钥等
```

---


## 四、运行指南

### 1. 环境准备

```bash
# 创建虚拟环境
conda create -n medicalQA python=3.10
# 安装依赖
pip install -u -r requirements.txt
```

### 2. 配置文件

- `.env` 文件示例：

```env
LLM_BASE_URL = https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_API_KEY=your_api_key
MODEL_NAME = doubao-1-5-pro-32k-250115
PY_ENVIRONMENT = web # yaml配置文件名后缀
```

- `config-web.yaml` 文件示例：
```yaml
# 知识库目录，存放知识库文件，如各种.pdf, .word文件
knowledge-path: ./backend/knowledges

# 向量库地址，存放文本向量文件
faiss-path: ./backend/faiss_index
 
model:
  graph-entity:
    # 知识图谱中检索实体时的搜索主键，即匹配这个键对应的值，根据知识图谱中实体的可检索属性
    search-key: 名称

  # 编码模型配置
  embedding: 
    # 构建知识库时用于文本向量化的模型路径，这里是一个本地路径
    path: backend/model
    name: bge-large-zh-v1.5
  
  # 重排模型配置
  rerank:
    path: backend/model
    name: bge-reranker-v2-m3

# 知识图谱配置
database:
  neo4j:
    url: bolt://localhost:7687
    database: you_database_name
    username: you_username
    password: you_password
    # 定义数据库存在的节点标签和关系类型，用于检索
    node-label: ['一级科室', '二级科室', '其他',"检查手段","治疗方案","生产商","疾病","症状","药物","食物","食谱"]
    relationship-type: ['好评药物', '宜吃', '属于', '常用药物', '并发症','忌吃','所属科室','推荐食谱','治疗方法','生产药品','症状','诊断建议']
```

### 3. 启动服务

```bash
uvicorn backend.main:app --reload
```

### 4. 访问地址

打开浏览器访问：`http://localhost:8000`

---

