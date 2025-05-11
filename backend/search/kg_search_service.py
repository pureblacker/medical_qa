from typing import Tuple, Optional, List,Dict
import ahocorasick as pyahocorasick
from backend.config.config import load_nested_params
from dataclasses import dataclass,field
from backend.Graph import GraphDao


@dataclass
class GetNodeEntities(object):
    # 该类负责与Graph类交互，获取节点信息

    dao: GraphDao = field(default_factory=lambda: GraphDao(), init=True, compare=False)

    # 获取图数据库中所有节点，以列表形式返回，列表中每个元素为一个字典，包含节点所属标签类和节点ID、名称等属性
    def get_entities_iterator(self):

        # 定义查询的标签类型，比如疾病、症状、药物等
        labels_to_query = load_nested_params("database", "neo4j", "node-label")

        node_list = []

        # 动态查询不同标签类型的节点
        for label in labels_to_query:
            # 查询带有特定标签的节点
            nodes = self.dao.query_node(label)

            for node in nodes:
                # 根据节点的标签和属性创建字典
                node_dict = {
                    'label': label,  # 使用当前查询的标签
                    **dict(node)  # 解包节点的属性
                }
                node_list.append(node_dict)

        return node_list
        
       
    def __call__(self, *args, **kwargs):
        return self.get_entities_iterator()


class EntitySearcher:

    def __init__(self, *args, **krgs):
        super().__init__(*args, **krgs)
        self._node_entities = GetNodeEntities()
        self._search_key = load_nested_params("model", "graph-entity", "search-key")
        self._model = None

        self.build()

    def build(self, *args, **kwargs):
        
        try:
            self._build_model()
        except Exception as e:
            raise RuntimeError("模型构建失败") from e

            
    def _build_model(self, *args, **kwargs):
        # pyahocorasick是一个快速且内存效率高的库，用于精确或近似多模式字符串搜索，
        # 可以根据输入文本，一次找到多个匹配关键字符串，字符串的索引提前构建并保存到磁盘中。
        automaton = pyahocorasick.Automaton()

        # self._node_entities 包含图数据库的节点信息，
        # 将节点的被检索属性作为用于匹配的字符串键，将（插入索引，原始字符串）的元组作为值关联到该字符串键。
        for i, entity in enumerate(self._node_entities()):
            automaton.add_word(entity[self._search_key], (i, entity))

        automaton.make_automaton()  # 构建自动机
        self._model = automaton  # 将自动机模型保存到实例变量中

    def search(self, query: str) -> Tuple[Optional[List[Dict]]]:

        results = []
        #自动机检索与查询字符串匹配的节点被检索属性，并返回匹配的节点信息
        for search_key, (insert_order, entity) in self._model.iter(query):
            results.append(entity)

        if results is not None:
            return 0 , results
        else:
            return -1 , None
    

