from dotenv import load_dotenv
from .kg_search_service import EntitySearcher
from typing import Callable, List, Dict, Tuple
from backend.config.config import load_nested_params
from backend.Graph import GraphDao
from backend.LLM.LLMclientgeneric import LLMclientgeneric

load_dotenv(".env", override=False)
_dao= GraphDao()
def relation_tool(entities: List[Dict] | None) -> str | None:
    if not entities or len(entities) == 0:
        return None

    relationships = set()  # 使用集合来避免重复关系
    relationship_match = []

    searchKey = load_nested_params("model", "graph-entity", "search-key")
    # 遍历每个实体并查询与其他实体的关系
    for entity in entities:
        entity_name = entity[searchKey]
        for k, v in entity.items():
            relationships.add(f"{entity_name} {k}: {v}")

        # 查询每个实体与其他实体的关系a-r-b
        relationship_match.append(_dao.query_relationship_by_name(entity_name))
        
    # 抽取并记录每个实体与其他实体的关系
    for i in range(len(relationship_match)):
        for record in relationship_match[i]:
            # 获取起始节点和结束节点的名称

            start_name = record["r"].start_node[searchKey]
            end_name = record["r"].end_node[searchKey]

            # 获取关系类型
            rel = type(record["r"]).__name__  # 获取关系名称，比如 CAUSES

            # 构建关系字符串并添加到集合，确保不会重复添加
            relationships.add(f"{start_name} {rel} {end_name}")

    # 返回关系集合的内容
    if relationships:
        return "；".join(relationships)
    else:
        return None

def check_entity(question: str) -> List[Dict]:
    code, result = EntitySearcher().search(question)
    if code == 0:
        return result
    else:
        return None


def KG_tool(
    question: str,
    history: List[List | None] = None,
):
    kg_info = None
    try:
        
        entities = check_entity(question) #利用pyahocorasick库检索问题中的实体
        kg_info = relation_tool(entities) #利用neo4j查询关系
    except:
        pass
        
    if kg_info is not None:
        print(f"KG_tool: \n {kg_info}")
        question = f"{question}\n从知识图谱中检索到的信息如下{kg_info}\n请你基于知识图谱的信息去回答,并给出知识图谱检索到的信息"

    response = LLMclientgeneric().chat_with_ai_stream(question, history)
    return response