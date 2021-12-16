from Pathfinder import *
import pysat
from pysat.solvers import MapleChrono
from pysat.formula import CNF

from Types import DiagramNode


class BDDiagram:
    def __init__(self,diagram:DisjunctiveDiagram):
        self.variable_count_ = diagram.variable_count_
        self.true_path_count_ = diagram.true_path_count_
        self.question_path_count_ = diagram.question_path_count_
        self.false_path_count_ = diagram.false_path_count_
        self.max_path_depth_ = diagram.max_path_depth_
        self.duplicate_reduced_ = diagram.duplicate_reduced_
        self.vertex_reduced_ = diagram.vertex_reduced_
        self.min_var_num_ = diagram.min_var_num_
        self.max_var_num_ = diagram.max_var_num_
        self.root_join_cnt_ = diagram.root_join_cnt_
        self.problem_type_ = diagram.problem_type_
        self.order_ = copy.copy(diagram.order_)
        self.table_ = copy.copy(diagram.table_)
        self.roots_ = copy.copy(diagram.roots_)
        self.main_root_ = None
        self.var_set_ = copy.copy(diagram.var_set_)
        BDD_convert(self)


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
        return self.table_[hash(tuple(['?']+[]+[]))]

    # Возвращает терминальный узел 1
    def GetTrueLeaf(self):
        return self.table_[hash(tuple(['true']+[]+[]))]

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

    def __del__(self):
        for node in self.table_:
            del node


def BDD_convert(diagram):
    # сперва надо свести корни к одному. для этого берём корень с наименьшим порядковым номером (относительно order)
    # затем добавляем ему ссылки на каждый другой корень причем и в high_childs и в low_childs
    roots_ = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_, diagram.roots_)
    main_root = roots_[-1]
    for root in roots_[:-1]:
        connect_roots(main_root, root)
    main_root.HashKey()
    diagram.main_root_ = main_root
    # Теперь вся диаграмма выходит из одного корня.

    # начинаем рекурсивно уводить связи вниз.
    stop_flag = True
    question_leaf = diagram.GetQuestionLeaf()
    true_leaf = diagram.GetTrueLeaf()
    while stop_flag == True:
        stop_flag = FindNonbinaryNodes(diagram, question_leaf)
    stop_flag = True
    while stop_flag == True:
        stop_flag = FindNonbinaryNodes(diagram, question_leaf)
    """
    Алгоритм (лучше):
    1. идем от теримнальной наверх, проверяем каждый node
    if len(node.high_childs) > 1:
        deleted_nodes = set()
        delete_nodes_from_table(node,deleted_nodes)
        upper_node, lower_node = find_upper_and_lower_childs(node.high_childs, order)
        delete_link_from_node(lower_node,node)
        create_link_from_lower_to_upper(lower_node,upper_node)
        sort_deleted_nodes_wrt_order(deleted_nodes,order)
        gluing_nodes(deleted_nodes)
    elif len(node.low_childs) > 1:
        deleted_nodes = set()
        delete_nodes_from_table(node,deleted_nodes)
        upper_node, lower_node = find_upper_and_lower_childs(node.high_childs, order)
        delete_link_from_node(lower_node,node)
        create_link_from_lower_to_upper(lower_node,upper_node)
        sort_deleted_nodes_wrt_order(deleted_nodes,order)
        gluing_nodes(deleted_nodes)
    """

def connect_roots(main_root, root):
    if root not in main_root.high_childs:
        main_root.high_childs.append(root)
        root.high_parents.append(main_root)
    if root not in main_root.low_childs:
        main_root.low_childs.append(root)
        root.low_parents.append(main_root)
    root.node_type = DiagramNodeType.InternalNode

# Рекурсивное удаление узлов из таблицы от node наверх
def DeletingNodesFromTable(node, diagram, deleted_nodes):
    deleted_nodes.add(node)
    del diagram.table_[node.hash_key]
    for parent in node.high_parents:
        DeletingNodesFromTable(parent, diagram, deleted_nodes)
    for parent in node.low_parents:
        DeletingNodesFromTable(parent, diagram, deleted_nodes)

# Получаем false paths из диаграммы (все пути из корней в терминальную '?')
def FindNonbinaryNodes(diagram:DisjunctiveDiagram, current_node):
    for node in current_node.high_parents + current_node.low_parents:
        if len(node.high_childs) > 1:
            deleted_nodes = set()
            DeletingNodesFromTable(node, diagram, deleted_nodes)
            upper_node, lower_node = find_upper_and_lower_childs(node.high_childs, diagram.order_)
            delete_link_from_node(lower_node, node)
            create_link_from_lower_to_upper(lower_node, upper_node)
            sort_deleted_nodes_wrt_order(deleted_nodes, diagram.order_)
            gluing_nodes(deleted_nodes)
            return True
        elif len(node.low_childs) > 1:
            deleted_nodes = set()
            DeletingNodesFromTable(node, diagram, deleted_nodes)
            upper_node, lower_node = find_upper_and_lower_childs(node.high_childs, diagram.order_)
            delete_link_from_node(lower_node, node)
            create_link_from_lower_to_upper(lower_node, upper_node)
            sort_deleted_nodes_wrt_order(deleted_nodes, diagram.order_)
            gluing_nodes(deleted_nodes)
            return True
        else:
            stop_flag = FindNonbinaryNodes(diagram, node)
            return stop_flag
    return False



