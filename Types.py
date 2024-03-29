from Imports import *


# Тип узла диаграммы
class DiagramNodeType(Enum):
    Undefined = 1
    RootNode = 2
    InternalNode = 3
    FalseNode = 4
    QuestionNode = 5
    TrueNode = 6


# Тип исходной формулы
class ProblemType(Enum):
    Conflict = 1
    Cnf = 2
    Dnf = 3


# Узел диаграммы
class DiagramNode:
    constructors_ = 0
    destructors_ = 0

    def __init__(self, Type:DiagramNodeType, VarId:int = None, HighChilds = None, LowChilds = None):
        if type(Type) == DiagramNodeType:
            self.node_type = Type
        else:
            raise Exception('Type of diagram node should be of the following: Undefined, RootNode, InternalNode, FalseNode, QuestionNode, TrueNode')
        self.var_id = 0 if VarId == None else VarId
        self.markup_varid = 0
        self.vertex_id = 0
        self.hash_key = 0
        self.high_childs = [] if HighChilds == None else sorted(copy.copy(HighChilds),key= lambda x:x.var_id)
        self.low_childs = [] if LowChilds == None else sorted(copy.copy(LowChilds),key= lambda x:x.var_id)
        self.high_parents = []
        self.low_parents = []
        self.HashKey()
        #print('Node',self.Value(), [x.Value() for x in self.high_childs], [x.Value() for x in self.low_childs])
        DiagramNode.constructors_ += 1

    # Вычисляет хэш узла (выполняется при создании узла)
    def HashKey(self):
        hashtuple_ = tuple([self.Value()]+[node.hash_key for node in self.high_childs]+[node.hash_key for node in self.low_childs])
        #print('hk',self.var_id,hashtuple_)
        self.hash_key = hash(hashtuple_)

    def __hash__(self):
        return self.hash_key

    # Сравнение узлов на основе их Value() и хэшей их потомков (не рекурсивно)
    def __eq__(self, other):
        if self.hash_key != other.hash_key:
            return False
        return True

    # Сравнение узлов на основе их потомков (рекурсивно)
    def Equals(self, other):
        if not isinstance(other, type(self)):
            return False
        if self.Value() != other.Value():
            return False
        if (len(self.high_childs) != len(other.high_childs) or
                len(self.low_childs) != len(other.low_childs)):
            return False
        for selfleft, nodeleft in zip(self.high_childs,other.high_childs):
            if not selfleft.Equals(nodeleft):
                return False
        for selfright, noderight in zip(self.low_childs,other.low_childs):
            if not selfright.Equals(noderight):
                return False
        return True

    # Возвращает размер узла в байтах
    def Size(self):
        return sys.getsizeof(self.Value()) + (8 * (len(self.high_childs) + len(self.low_childs)))

    # Возвращает номер переменный для внутренних и корневых узлов, либо строковые значения для терминальных
    def Value(self):
        if self.node_type == DiagramNodeType.InternalNode or self.node_type == DiagramNodeType.RootNode:
            return self.var_id
        elif self.node_type == DiagramNodeType.QuestionNode:
            return '?'
        elif self.node_type == DiagramNodeType.TrueNode:
            return 'true'
        else:
            return 'false'


    # Проверяет является ли узел терминальным
    def IsLeaf(self):
        return True if (self.node_type == DiagramNodeType.TrueNode or
                        self.node_type == DiagramNodeType.QuestionNode or
                        self.node_type == DiagramNodeType.FalseNode) else False

    # Проверяет является ли узел корневым
    def IsRoot(self):
        return True if (self.node_type == DiagramNodeType.RootNode) else False

    # Првоеряет является ли узел внутренним
    def IsInternal(self):
        return True if (self.node_type == DiagramNodeType.InternalNode) else False

    def __del__(self):
        DiagramNode.destructors_ += 1


# Таблица с узлами диаграммы
class DisjunctiveDiagram:
    true_leaf = DiagramNode(DiagramNodeType.TrueNode)
    #false_leaf = DiagramNode(DiagramNodeType.FalseNode)
    question_leaf = DiagramNode(DiagramNodeType.QuestionNode)
    def __init__(self):
        self.variable_count_ = 0
        self.true_path_count_ = 0
        self.question_path_count_ = 0
        self.false_path_count_ = 0
        self.max_path_depth_ = 0
        self.duplicate_reduced_ = 0
        self.vertex_reduced_ = 0
        self.min_var_num_ = 0
        self.max_var_num_ = 0
        self.root_join_cnt_ = 0
        self.problem_type_ = None
        self.table_ = {}
        self.roots_ = set()
        self.var_set_ = set()
        self.table_[DisjunctiveDiagram.true_leaf.hash_key] = DisjunctiveDiagram.true_leaf
        self.table_[DisjunctiveDiagram.question_leaf.hash_key] = DisjunctiveDiagram.question_leaf


    # Возвращает таблицу
    def GetTable(self):
        return self.table_

    # Возвращает множество корней
    def GetRoots(self):
        return self.roots_

    # Возращает тип исходной формулы: кнф, днф, конфликтная база
    def GetProblemType(self):
        return self.problem_type_

    # Возвращает число переменных
    def VariableCount(self):
        return len(self.var_set_)

    # Возвращает переменную с наименьшим номером
    def MinVarId(self):
        return self.var_set_[0] if len(self.var_set_) > 0 else 0

    # Возвращает переменную с наибольшим номером
    def MaxVarId(self):
        return self.var_set_[-1] if len(self.var_set_) > 0 else 0

    # Возвращает число вершин в диаграмме
    def VertexCount(self):
        return len(self.table_)

    # Возвращает число путей в 1
    def TruePathCount(self):
        return self.true_path_count_

    # Возвращает число путей в ?
    def QuestionPathCount(self):
        return self.question_path_count_

    # Возвращает число путей в 0
    def FalsePathCount(self):
        return self.false_path_count_

    # Возвращает максимальную длину пути
    def MaxPathDepth(self):
        return self.max_path_depth_

    # Возвращает терминальный узел ?
    def GetQuestionLeaf(self):
        return DisjunctiveDiagram.question_leaf

    # Возвращает терминальный узел 1
    def GetTrueLeaf(self):
        return DisjunctiveDiagram.true_leaf

    # Возвращает терминальный узел 0
    def GetFalseLeaf(self):
        return DisjunctiveDiagram.false_leaf

    # Возвращается число удаленных узлов изза дупликации потомков (когда потомки совпадают по ребрам разной полярности)
    def DuplicateReducedCount(self):
        return self.duplicate_reduced_

    def VertexReducedCount(self):
        return self.vertex_reduced_

    def RootJoinCount(self):
        return self.root_join_cnt_

    # Возвращает размер диаграммы в байтах
    def DiagramSize(self):
        size = 0
        for node in self.table_:
            size += node.Size()
        return size

    def PrintCurrentTable(self):
        for node in self.table_.values():
            print("Node", node.vertex_id, " var", node.Value(), "hc:",[(x.vertex_id,x.Value()) for x in node.high_childs], "lc:",[(x.vertex_id,x.Value()) for x in node.low_childs])

    def __del__(self):
        for node in self.table_:
            del node


class Options:
    def __init__(self):
        self.path = 'Tests/test1.cnf'
        self.filename = 'test1.cnf'
        self.suffix = 'cnf'
        self.name = 'test1'
        self.dir = "./Tests"
        self.analyze_log = "result.txt"
        self.analyze_var_limit = 20
        self.analyze_var_fraction = 0.5
        self.source_type = "conflicts"
        self.order_type = "header"
        self.run_tests = False
        self.show_statistic = False
        self.show_version = False
        self.show_options = False
        self.bdd_convert = False
        self.redir_paths = False
        self.lock_vars = False