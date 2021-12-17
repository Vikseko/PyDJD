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

    def PrintCurrentTable(self):
        for node in self.table_.values():
            print("Node", node.vertex_id, " var", node.Value(), "hc:",[(x.vertex_id,x.Value()) for x in node.high_childs], "lc:",[(x.vertex_id,x.Value()) for x in node.low_childs])

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
        find_flag = False
        stop_flag = FindNonbinaryNodes(diagram, question_leaf, find_flag)
        print('')
        BDDiagram.PrintCurrentTable(diagram)
    stop_flag = True
    while stop_flag == True:
        find_flag = False
        stop_flag = FindNonbinaryNodes(diagram, question_leaf, find_flag)
        BDDiagram.PrintCurrentTable(diagram)

def connect_roots(main_root, root):
    if root not in main_root.high_childs:
        main_root.high_childs.append(root)
        root.high_parents.append(main_root)
    if root not in main_root.low_childs:
        main_root.low_childs.append(root)
        root.low_parents.append(main_root)
    root.node_type = DiagramNodeType.InternalNode

# Получаем false paths из диаграммы (все пути из корней в терминальную '?')
def FindNonbinaryNodes(diagram:DisjunctiveDiagram, current_node, find_flag):
    if find_flag == True:
        return True
    for node in current_node.high_parents + current_node.low_parents:
        if len(node.high_childs) > 1:
            GettingRidOfNonbinary(diagram, node, 1)
            find_flag = True
            return True
        elif len(node.low_childs) > 1:
            GettingRidOfNonbinary(diagram, node, 0)
            find_flag = True
            return True
        else:
            stop_flag = FindNonbinaryNodes(diagram, node, find_flag)
            #return stop_flag
    return False

def GettingRidOfNonbinary(diagram:DisjunctiveDiagram, node, polarity):
    if polarity == 1:
        childs = node.high_childs
    else:
        childs = node.low_childs
    deleted_nodes = set()
    upper_node, lower_node = FindUpperAndLowerChilds(childs, diagram.order_)
    DeletingNodesFromTable(upper_node, diagram, deleted_nodes)
    DeleteLinkFromNode(lower_node, node, polarity)
    CreateLinkBetweenLowerToUpper(lower_node, upper_node)
    deleted_nodes = LitLessSortNodes(deleted_nodes, diagram.order_)
    GluingNodes(deleted_nodes, diagram)

# Рекурсивное удаление узлов из таблицы от node наверх
def DeletingNodesFromTable(node, diagram, deleted_nodes):
    deleted_nodes.add(node)
    del diagram.table_[node.hash_key]
    for parent in node.high_parents:
        DeletingNodesFromTable(parent, diagram, deleted_nodes)
    for parent in node.low_parents:
        DeletingNodesFromTable(parent, diagram, deleted_nodes)

#находим у небинарного узла верхнего и нижнего потомка по небинарной полярности
def FindUpperAndLowerChilds(childs, order):
    sorted_childs = LitLessSortNodes(set(childs),order)
    lower = sorted_childs[0]
    upper = sorted_childs[-1]
    return upper, lower

#Сортировка множества узлов w.r.t. order
def LitLessSortNodes(nodes:set,order:list):
    nodes = list(nodes)
    sorted_nodes = [node for x in order for node in nodes if node.Value() == x]
    return sorted_nodes

#удаляем связь между небинарным узлом и нижним потомком по небинарной полярности
def DeleteLinkFromNode(lower_node, node, polarity):
    if polarity == 1:
        node.high_childs = [x for x in node.high_childs if x is not lower_node]
        lower_node.high_parents = [x for x in lower_node.high_parents if x is not node]
    else:
        node.low_childs = [x for x in node.low_childs if x is not lower_node]
        lower_node.low_parents = [x for x in lower_node.low_parents if x is not node]

def CreateLinkBetweenLowerToUpper(lower_node, upper_node):
    if upper_node not in lower_node.high_parents:
        lower_node.high_parents.append(upper_node)
    if upper_node not in lower_node.low_parents:
        lower_node.low_parents.append(upper_node)
    if lower_node not in upper_node.high_childs:
        upper_node.high_childs.append(lower_node)
    if lower_node not in upper_node.low_childs:
        upper_node.low_childs.append(lower_node)

def GluingNodes(deleted_nodes, diagram):
    deleted_nodes = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_, deleted_nodes)
    for node in deleted_nodes:
        node.HashKey()
        if node.hash_key in diagram.table_ and diagram.table_[node.hash_key] is not node:
            it_node = diagram.table_[node.hash_key]
            if node is it_node:
                print('ERROR')
            #print('Glued node',(node.Value(), node),'with node',(it_node.Value(),it_node))
            GluingNode(node,it_node)
            del node
        else:
            diagram.table_[node.hash_key] = node

def GluingNode(node,it_node):
    # заменяем ссылки в родителях
    ReplaceParentsLinksToNode(node,it_node)
    # Удаляем ссылки потомков узла на него
    DeleteChildsLinksToNode(node)
    # Заменяем узел в node_paths
    #ReplaceNodeInNodePaths(node,it_node,node_paths)

def ReplaceParentsLinksToNode(node,it_node):
    for parent in node.high_parents:
        parent.high_childs = [x for x in parent.high_childs if x is not node and x is not it_node]
        parent.high_childs.append(it_node)
        for tmpnode in it_node.high_parents:
            if tmpnode is parent:
                break
        else:
            #print('add as highparent ', (parent.Value(), parent), 'to node', (it_node.Value(), it_node))
            it_node.high_parents.append(parent)
    for parent in node.low_parents:
        parent.low_childs = [x for x in parent.low_childs if x is not node and x is not it_node]
        parent.low_childs.append(it_node)
        for tmpnode in it_node.low_parents:
            if tmpnode is parent:
                break
        else:
            it_node.low_parents.append(parent)
            #print('add as lowparent ', (parent.Value(), parent), 'to node', (it_node.Value(), it_node))

def DeleteChildsLinksToNode(node):
    for child in node.high_childs:
        child.high_parents = [x for x in child.high_parents if x is not node]
    for child in node.low_childs:
        child.low_parents = [x for x in child.low_parents if x is not node]

