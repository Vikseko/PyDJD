import copy
import sys
from enum import Enum

class DiagramNodeType(Enum):
    Undefined = 1
    RootNode = 2
    InternalNode = 3
    FalseNode = 4
    QuestionNode = 5
    TrueNode = 6

class ProblemType(Enum):
    Conflict = 1
    Cnf = 2
    Dnf = 3

#Узел диаграммы
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
        self.high_childs = [] if HighChilds == None else sorted(copy.copy(HighChilds))
        self.low_childs = [] if LowChilds == None else sorted(copy.copy(LowChilds))
        self.high_parents = []
        self.low_parents = []
        self.HashKey()
        DiagramNode.constructors_ += 1

    def HashKey(self):
        hashtuple_ = tuple([self.Value()]+[node.hash_key for node in self.high_childs]+[node.hash_key for node in self.low_childs])
        print('hk',self.var_id,hashtuple_)
        self.hash_key = hash(hashtuple_)

    def __hash__(self):
        return self.hash_key

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        if self.Value() != other.Value():
            return False
        if (len(self.high_childs) != len(other.high_childs) or
                len(self.low_childs) != len(other.low_childs)):
            return False
        for selfleft, nodeleft in zip(self.high_childs,other.high_childs):
            if selfleft.hash_key != nodeleft.hash_key:
                return False
        for selfright, noderight in zip(self.low_childs,other.low_childs):
            if selfright.hash_key != noderight.hash_key:
                return False
        return True

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

    def Size(self):
        return sys.getsizeof(self.Value()) + (8 * (len(self.high_childs) + len(self.low_childs)))

    def Value(self):
        if self.node_type == DiagramNodeType.InternalNode:
            return self.var_id
        elif self.node_type == DiagramNodeType.FalseNode:
            return 'false'
        elif self.node_type == DiagramNodeType.QuestionNode:
            return '?'
        elif self.node_type == DiagramNodeType.TrueNode:
            return 'true'

    def IsLeaf(self):
        return True if (self.node_type == DiagramNodeType.TrueNode or
                        self.node_type == DiagramNodeType.QuestionNode or
                        self.node_type == DiagramNodeType.FalseNode) else False

    def IsRoot(self):
        return True if (self.node_type == DiagramNodeType.RootNode) else False

    def IsInternal(self):
        return True if (self.node_type == DiagramNodeType.InternalNode) else False

    def __del__(self):
        DiagramNode.destructors_ += 1

#Таблица с узлами диаграммы
class DisjunctiveDiagram:
    true_leaf = DiagramNode(DiagramNodeType.TrueNode)
    false_leaf = DiagramNode(DiagramNodeType.FalseNode)
    question_leaf = DiagramNode(DiagramNodeType.QuestionNode)
    def __init__(self):
        self.variable_count_ = 0
        self.true_path_count_ = 0
        self.false_path_count_ = 0
        self.max_path_depth_ = 0
        self.duplicate_reduced_ = 0
        self.vertex_reduced_ = 0
        self.min_var_num_ = 0
        self.max_var_num_ = 0
        self.root_join_cnt_ = 0
        self.problem_type_ = None
        self.table_ = set()
        self.roots_ = set()
        self.var_set_ = []
        self.table_.add(DisjunctiveDiagram.true_leaf)
        self.table_.add(DisjunctiveDiagram.false_leaf)
        self.table_.add(DisjunctiveDiagram.question_leaf)

    def GetTable(self):
        return self.table_

    def GetRoots(self):
        return self.roots_

    def GetProblemType(self):
        return self.problem_type_

    def VariableCount(self):
        return len(self.var_set_)

    def MinVarId(self):
        return self.var_set_[0] if self.var_set_.size() > 0 else 0

    def MaxVarId(self):
        return self.var_set_[-1] if self.var_set_.size() > 0 else 0

    def GetQuestionLeaf(self):
        return DisjunctiveDiagram.question_leaf

    def GetTrueLeaf(self):
        return DisjunctiveDiagram.true_leaf

    def GetFalseLeaf(self):
        return DisjunctiveDiagram.false_leaf

    def DiagramSize(self):
        size = 0
        for node in self.table_:
            size += node.Size()
        return size


    def __del__(self):
        for node in self.table_:
            del node

#Функция по элементу ищет в множестве такой же и возвращает его (проверять наличие нужно отдельно)
def get_equivalent(container, item):
    for element in container:
        if element == item:
            return element

class Options:
    def __init__(self):
        self.analyze_log = "result.txt"
        self.analyze_var_limit = 20
        self.analyze_var_fraction = 0.5
        self.dir = "./"
        self.source = "conflicts"
        self.order = "header"
        self.run_tests = False
        self.show_statistic = False
        self.show_version = False
        self.show_options = False
        self.show_help = False