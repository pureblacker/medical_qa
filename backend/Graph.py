'''实例化知识图谱对象'''
from backend.config.config import load_nested_params
from py2neo import Graph, NodeMatcher, RelationshipMatcher, ConnectionUnavailable

class GraphDao(object):

    def __init__(self):
        # 读取yaml配置
        self.url = load_nested_params("database", "neo4j", "url")
        self.username = load_nested_params("database", "neo4j", "username")
        self.password = load_nested_params("database", "neo4j", "password")
        self.connect_graph()

        # 创建节点匹配器
        self.node_matcher = NodeMatcher(self.graph) if self.graph else None

        # 创建关系匹配器
        self.relationship_matcher = RelationshipMatcher(self.graph) if  self.graph else None

    @staticmethod
    def ensure_connection(function):
        def wrapper(*args, **kwargs):
            if not args[0].graph:
                return None
            return function(*args, **kwargs)

        return wrapper

    def connect_graph(self):
        try:
            self.graph = Graph(self.url, auth=(self.username, self.password))
        except ConnectionUnavailable as e:
            self.graph = None
    
    @ensure_connection
    def query_relationship_by_name(self, entity_name: str):
        # 编写 Cypher 查询语句，查询指定实体作为起始或目标节点的所有关系
        query = """
        MATCH (a)-[r]-(b)
        WHERE a.名称 = $entity_name
        RETURN a,r,b
        """
        # 执行查询，并将查询结果返回
        result = self.graph.run(query, entity_name=entity_name).data()
        return result
    
    @ensure_connection
    def query_node(self, *label, **properties):
        return self.node_matcher.match(*label, **properties)

# Graph_ = GraphDao()
# print(Graph_.password)
# print(Graph_.query_relationship_by_name('糖尿病'))