from Pathfinder import *
import pysat
from pysat.solvers import MapleChrono
from pysat.formula import CNF

from Types import DiagramNode


class BDDiagram:
    new_nodes_ = 0
    deleted_nodes_ = 0
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
        CleaningDiagram(self)
        try:
            question_leaf = self.GetQuestionLeaf()
            print(question_leaf.Value(), [x.Value() for x in question_leaf.high_parents],[x.Value() for x in question_leaf.low_parents])
        except:
            print('woops')
        EnumerateBDDiagramNodes(self)


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

    def NonBinaryLinkCount(self):
        counter = 0
        for node in self.table_.values():
            if len(node.high_childs) > 1:
                counter += len(node.high_childs) - 1
            if len(node.low_childs) > 1:
                counter += len(node.low_childs) - 1
        return counter

    def NonBinaryNodesCount(self):
        counter = 0
        for node in self.table_.values():
            if len(node.high_childs) > 1:
                counter += 1
            elif len(node.low_childs) > 1:
                counter += 1
        return counter

    def PrintCurrentTable(self):
        print('')
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

def EnumerateBDDiagramNodes(diagram):
    vertex_id = 0
    for node in diagram.table_.values():
        vertex_id += 1
        node.vertex_id = vertex_id

def BDD_convert(diagram):
    # сперва надо свести корни к одному. для этого берём корень с наименьшим порядковым номером (относительно order)
    # затем добавляем ему ссылки на каждый другой корень причем и в high_childs и в low_childs
    print('Initial number of nonbinary links in diagram is', BDDiagram.NonBinaryLinkCount(diagram))
    print('Initial number of nonbinary nodes in diagram is', BDDiagram.NonBinaryNodesCount(diagram))
    roots_ = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_, diagram.roots_)
    main_root = roots_[-1]
    for i in range(len(roots_)-1):
        ConnectRoots(roots_[i+1], roots_[i],diagram)
    del diagram.table_[main_root.hash_key]
    main_root.HashKey()
    diagram.table_[main_root.hash_key] = main_root
    diagram.main_root_ = main_root
    print('Main root number:', main_root.vertex_id,'; variable:',main_root.var_id)
    print('Number of nonbinary links in diagram after roots gluing is', BDDiagram.NonBinaryLinkCount(diagram))
    print('Number of nonbinary nodes in diagram after roots gluing is', BDDiagram.NonBinaryNodesCount(diagram))
    # Теперь вся диаграмма выходит из одного корня.
    # начинаем рекурсивно уводить связи вниз.
    stop_flag = True
    question_leaf = diagram.GetQuestionLeaf()
    BDDiagram.PrintCurrentTable(diagram)
    while BDDiagram.NonBinaryNodesCount(diagram) > 0:
        nodes = diagram.table_.values()
        nodes = reversed(DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_, nodes))
        for node in nodes:
            # stop_flag = FindNonbinaryNodesFromTerminal(diagram, question_leaf)
            stop_flag = FindNonbinaryNodesInTable(diagram, node)
            if stop_flag == True:
                break
    """
    while stop_flag == True:
    #while BDDiagram.NonBinaryNodesCount(diagram) > 0:
        print('')
        print('Current number of nonbinary links is',BDDiagram.NonBinaryLinkCount(diagram))
        print('Current number of nonbinary nodes is',BDDiagram.NonBinaryNodesCount(diagram))
        #stop_flag = FindNonbinaryNodesFromTerminal(diagram, question_leaf)
        stop_flag = FindNonbinaryNodesFromRoot(diagram, main_root)
        #BDDiagram.PrintCurrentTable(diagram)
    """
    """
    stop_flag = True
    true_leaf = diagram.GetTrueLeaf()
    while stop_flag == True:
        print('')
        print('Current number of nonbinary links is',BDDiagram.NonBinaryLinkCount(diagram))
        print('Current number of nonbinary nodes is',BDDiagram.NonBinaryNodesCount(diagram))
        stop_flag = FindNonbinaryNodesFromTerminal(diagram, true_leaf)
        #BDDiagram.PrintCurrentTable(diagram)
    """

def ConnectRoots(upper, lower,diagram):
    deleted_nodes = set()
    ConnectNodesDouble(lower,upper,deleted_nodes,diagram)
    lower.node_type = DiagramNodeType.InternalNode
    if upper.hash_key in diagram.table_:
        del diagram.table_[upper.hash_key]
    upper.HashKey()
    diagram.table_[upper.hash_key] = upper

def ConnectNodesDouble(lower, upper, deleted_nodes, diagram):
    high_glu = False
    candidates_to_deletion = set()
    if diagram.GetTrueLeaf() not in upper.high_childs:
        for node in upper.high_childs:
            if node.Value() == lower.Value():
                high_glu = True
                TransferChilds(lower,upper,node,deleted_nodes,candidates_to_deletion,diagram)
                break
        else:
            upper.high_childs.append(lower)
            lower.high_parents.append(upper)
            DeletingNodesFromTable(upper, diagram, deleted_nodes)
    else:
        high_glu = True
    low_glu = False
    if diagram.GetTrueLeaf() not in upper.low_childs:
        for node in upper.low_childs:
            if node.Value() == lower.Value():
                low_glu = True
                #вот тут надо передать всех детей ловера апперу в high_childs,
                # причем рекурсивно проверять условия дублирования детей
                TransferChilds(lower,upper,node,deleted_nodes,candidates_to_deletion,diagram)
                break
        else:
            upper.low_childs.append(lower)
            lower.low_parents.append(upper)
            DeletingNodesFromTable(upper, diagram, deleted_nodes)
    else:
        low_glu = True
    if high_glu == True and low_glu == True:
        # нужно удалить сам узел, сперва проверив, что у него нет родителей и удалив его из родителей его детей,
        # затем рекурсивно првоерить детей на то, что если родителей больше нет, то удаляем и эти излы и тд
        RecursiveDeletionNodesFromDiagram(lower,diagram)

def TransferChilds(from_node,upper,to_node,deleted_nodes,candidates_to_deletion,diagram):
    copy_flag = False
    for parent in to_node.high_parents + to_node.low_parents:
        if parent is not upper:
            copy_flag = True
            break
    if copy_flag == True:
        diagram.new_nodes_ += 1
        new_node = CopyNodeWithoutLinkToUpper(to_node, upper)
    if diagram.GetTrueLeaf() not in to_node.high_childs:
        for from_child in from_node.high_childs:
            for to_child in to_node.high_childs:
                if from_child.Value() == to_child.Value():
                    candidates_to_deletion.add(from_child)
                    TransferChilds(from_child,to_node,to_child,deleted_nodes,candidates_to_deletion,diagram)
                    break
            else:
                to_node.high_childs.append(from_child)
                from_child.high_parents.append(to_node)
    else:
        candidates_to_deletion.update(from_node.high_childs)
        # тут нужно какимто образом удалить потомков, если они больше не нужны нигде (нужна вот эта проверка на нужность)
    if diagram.GetTrueLeaf() not in to_node.low_childs:
        for from_child in from_node.low_childs:
            for to_child in to_node.low_childs:
                if from_child.Value() == to_child.Value():
                    candidates_to_deletion.add(from_child)
                    TransferChilds(from_child,to_node, to_child, deleted_nodes,candidates_to_deletion,diagram)
                    break
            else:
                to_node.low_childs.append(from_child)
                from_child.low_parents.append(to_node)
    else:
        candidates_to_deletion.update(from_node.low_childs)
        # тут нужно какимто образом удалить потомков, если они больше не нужны нигде (нужна вот эта проверка на нужность)
    if copy_flag == True:
        deleted_nodes = set([x for x in deleted_nodes if x is not to_node])
        to_node.HashKey()
        deleted_nodes.add(to_node)
        deleted_nodes.add(new_node)


def CopyNodeWithoutLinkToUpper(original_node, upper):
    new_node = DiagramNode(original_node.node_type, original_node.var_id, original_node.high_childs,
                           original_node.low_childs)
    new_node.high_parents = [parent for parent in original_node.high_parents if parent is not upper]
    for node in new_node.high_parents:
        node.high_childs = [x for x in node.high_childs if x is not original_node]
    new_node.low_parents = [parent for parent in original_node.low_parents if parent is not upper]
    for node in new_node.low_parents:
        node.low_childs = [x for x in node.low_childs if x is not original_node]
    original_node.high_parents = [node for node in original_node.high_parents if node is upper]
    original_node.low_parents = [node for node in original_node.low_parents if node is upper]
    for parent in new_node.high_parents:
        parent.high_childs.append(new_node)
    for parent in new_node.low_parents:
        parent.low_childs.append(new_node)
    for child in new_node.high_childs:
        child.high_parents.append(new_node)
    for child in new_node.low_childs:
        child.low_parents.append(new_node)
    return new_node

def RecursiveDeletionNodesFromDiagram(lower,diagram):
    if lower.node_type is not DiagramNodeType.QuestionNode \
            and lower.node_type is not DiagramNodeType.TrueNode\
            and len(lower.high_parents) == 0\
            and len(lower.low_parents) == 0:
        for child in lower.high_childs:
            child.high_parents = [x for x in child.high_parents if x is not lower]
            RecursiveDeletionNodesFromDiagram(child,diagram)
        for child in lower.low_childs:
            child.low_parents = [x for x in child.low_parents if x is not lower]
            RecursiveDeletionNodesFromDiagram(child,diagram)
        if lower.hash_key in diagram.table_:
            #print('del from table', (lower.vertex_id, lower.Value()))
            del diagram.table_[lower.hash_key]
            #if lower.hash_key in diagram.table_:
                #print('ERROR NO DEL')
        print('del node', (lower.vertex_id, lower.Value()))
        diagram.deleted_nodes_ += 1
        del lower


def FindNonbinaryNodesFromTerminal(diagram:DisjunctiveDiagram, current_node):
    find_flag = False
    for node in current_node.high_parents + current_node.low_parents:
        if len(node.high_childs) > 1:
            """
            print('Find nonbinary node:', (node.vertex_id, node.Value()), 'hc', "hc:", [(x.vertex_id, x.Value()) for x in
                                                                  node.high_childs], "lc:", [(x.vertex_id, x.Value())
                                                                                             for x in node.low_childs])
            """
            GettingRidOfNonbinary(diagram, node, 1)
            find_flag = True
            break
        elif len(node.low_childs) > 1:
            """
            print('Find nonbinary node:', (node.vertex_id, node.Value()), 'lc', "hc:", [(x.vertex_id, x.Value()) for x in
                                                                  node.high_childs], "lc:", [(x.vertex_id, x.Value())
                                                                                             for x in node.low_childs])
            """
            GettingRidOfNonbinary(diagram, node, 0)
            find_flag = True
            break
        else:
            find_flag = FindNonbinaryNodesFromTerminal(diagram, node)
            if find_flag == True:
                return True
    if find_flag == True:
        return True
    return False

def GettingRidOfNonbinary(diagram:DisjunctiveDiagram, node, polarity):
    if polarity == 1:
        childs = node.high_childs
    else:
        childs = node.low_childs
    deleted_nodes = set()
    upper_node, lower_node = FindUpperAndLowerChilds(childs, diagram.order_)
    print('Upper node:', (upper_node.vertex_id, upper_node.Value()),'Lower node:', (lower_node.vertex_id, lower_node.Value()))
    DeletingNodesFromTable(upper_node, diagram, deleted_nodes)
    DeleteLinkFromNode(lower_node, node, polarity)
    if lower_node is not diagram.GetQuestionLeaf() \
            and upper_node is not diagram.GetTrueLeaf() \
            and upper_node is not diagram.GetQuestionLeaf():
        ConnectNodesDouble(lower_node, upper_node, deleted_nodes, diagram)
    elif upper_node is diagram.GetTrueLeaf():
        RecursiveDeletionNodesFromDiagram(lower_node,diagram)
    deleted_nodes = LitLessSortNodes(deleted_nodes, diagram.order_)
    GluingNodes(deleted_nodes, diagram)

# Рекурсивное удаление узлов из таблицы от node наверх
def DeletingNodesFromTable(node, diagram, deleted_nodes):
    deleted_nodes.add(node)
    if node.hash_key in diagram.table_ and node is not diagram.GetTrueLeaf() and node is not diagram.GetQuestionLeaf():
        del diagram.table_[node.hash_key]
        for parent in set(node.high_parents+node.low_parents):
            DeletingNodesFromTable(parent, diagram, deleted_nodes)
    #for parent in node.low_parents:
        #DeletingNodesFromTable(parent, diagram, deleted_nodes)

#находим у небинарного узла верхнего и нижнего потомка по небинарной полярности
def FindUpperAndLowerChilds(childs, order):
    sorted_childs = LitLessSortNodes(set(childs),order)
    lower = sorted_childs[0]
    upper = sorted_childs[1]
    return upper, lower


#Сортировка множества узлов w.r.t. order
def LitLessSortNodes(nodes:set,order:list):
    nodes = list(nodes)
    #print('nodes',nodes)
    #print('order',order)
    sorted_nodes = [node for x in order for node in nodes if node.Value() == x]
    #print('sorted nodes',sorted_nodes)
    #exit()
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
            diagram.deleted_nodes_ += 1
            print('del glu node',(node.Value(), node))
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


def FindNonbinaryNodesFromRoot(diagram:DisjunctiveDiagram, current_node):
    find_flag = False
    if len(current_node.high_childs) > 1:

        print('Find nonbinary node:', (current_node.vertex_id, current_node.Value()), 'hc', "hc:", [(x.vertex_id, x.Value()) for x in
                                                            current_node.high_childs], "lc:", [(x.vertex_id, x.Value())
                                                                                        for x in current_node.low_childs])

        GettingRidOfNonbinary(diagram, current_node, 1)
        find_flag = True
    elif len(current_node.low_childs) > 1:

        print('Find nonbinary node:', (current_node.vertex_id, current_node.Value()), 'lc', "hc:", [(x.vertex_id, x.Value()) for x in
                                                            current_node.high_childs], "lc:", [(x.vertex_id, x.Value())
                                                                                        for x in current_node.low_childs])

        GettingRidOfNonbinary(diagram, current_node, 0)
        find_flag = True
    if find_flag == True:
        return True
    for node in current_node.high_childs + current_node.low_childs:
        find_flag = FindNonbinaryNodesFromRoot(diagram, node)
        if find_flag == True:
            return True
    return False

def FindNonbinaryNodesInTable(diagram, current_node):
    find_flag = False
    if len(current_node.high_childs) > 1:
        print('')
        print('Current number of nonbinary links is', BDDiagram.NonBinaryLinkCount(diagram))
        print('Current number of nonbinary nodes is', BDDiagram.NonBinaryNodesCount(diagram))
        print('Find nonbinary node:', (current_node.vertex_id, current_node.Value()), 'hc', "hc:", [(x.vertex_id, x.Value()) for x in
                                                            current_node.high_childs], "lc:", [(x.vertex_id, x.Value())
                                                                                        for x in current_node.low_childs])
        GettingRidOfNonbinary(diagram, current_node, 1)
        find_flag = True
    elif len(current_node.low_childs) > 1:
        print('')
        print('Current number of nonbinary links is', BDDiagram.NonBinaryLinkCount(diagram))
        print('Current number of nonbinary nodes is', BDDiagram.NonBinaryNodesCount(diagram))
        print('Find nonbinary node:', (current_node.vertex_id, current_node.Value()), 'lc', "hc:", [(x.vertex_id, x.Value()) for x in
                                                            current_node.high_childs], "lc:", [(x.vertex_id, x.Value())
                                                                                        for x in current_node.low_childs])
        GettingRidOfNonbinary(diagram, current_node, 0)
        find_flag = True
    if find_flag == True:
        return True
    return False

def CleaningDiagram(diagram):
    all_nodes = sorted([node for node in diagram.table_.values()], key=lambda x: x.vertex_id)
    while len(all_nodes) > 0:
        node = all_nodes[0]
        all_nodes = all_nodes[1:]
        print('lenb',len(all_nodes))
        print('Check node', node.vertex_id, node.var_id)
        RecursiveCleaningNodesFromDiagram(node,diagram)
        print('lena', len(all_nodes))

def RecursiveCleaningNodesFromDiagram(node,diagram):
    if node.node_type is not DiagramNodeType.RootNode\
            and len(node.high_parents) == 0\
            and len(node.low_parents) == 0:
        for child in node.high_childs:
            child.high_parents = [x for x in child.high_parents if x is not node]
            RecursiveCleaningNodesFromDiagram(child,diagram)
        for child in node.low_childs:
            child.low_parents = [x for x in child.low_parents if x is not node]
            RecursiveCleaningNodesFromDiagram(child,diagram)
        if node.hash_key in diagram.table_:
            #print('del from table', (node.vertex_id, node.Value()))
            del diagram.table_[node.hash_key]
            if node.hash_key in diagram.table_:
                print('ERROR NO DEL')
        print('del node', (node.vertex_id, node.Value()))
        diagram.deleted_nodes_ += 1
        del node