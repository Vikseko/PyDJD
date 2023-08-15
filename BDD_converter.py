from Pathfinder import *
import pysat
from pysat.solvers import MapleChrono
from pysat.formula import CNF
from Draw import *

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
        except Exception:
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
        return self.table_[hash('questionnode')]

    # Возвращает терминальный узел 1
    def GetTrueLeaf(self):
        return self.table_[hash('truenode')]

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
        for node in self.table_.values():
            print("Node", node.vertex_id,
                "var", node.Value(),
                node.node_type,
                "hc:", [(x.vertex_id, x.Value()) for x in node.high_childs],
                "lc:", [(x.vertex_id, x.Value()) for x in node.low_childs])
        print()

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
    sorted_roots_ = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_, diagram.roots_)
    print('Roots', [(x.vertex_id, x.var_id, x.node_type) for x in diagram.roots_])
    print('\nTable before roots gluing:')
    BDDiagram.PrintCurrentTable(diagram)
    main_root = sorted_roots_[-1]
    for i in range(len(sorted_roots_)-1):
        print('Connect root', str(sorted_roots_[i].vertex_id) + '_' + str(sorted_roots_[i].var_id), ' to root', str(sorted_roots_[i+1].vertex_id) + '_' + str(sorted_roots_[i+1].var_id))
        # присоединяем нижний корень к верхнему по двум полярностям
        ConnectRoots(sorted_roots_[i+1], sorted_roots_[i],diagram)
    # теперь diagram.roots_ неправильная, потому что хэши поменялись (бтв, в table всё обновлено), но это и неважно
    print('Roots', [(x.vertex_id, x.var_id, x.node_type) for x in diagram.roots_])
    diagram.main_root_ = main_root
    print('Main root number:', main_root.vertex_id,'; variable:',main_root.var_id)
    print('Number of nonbinary links in diagram after roots gluing is', BDDiagram.NonBinaryLinkCount(diagram))
    print('Number of nonbinary nodes in diagram after roots gluing is', BDDiagram.NonBinaryNodesCount(diagram))
    print('\nTable after roots gluing:')
    BDDiagram.PrintCurrentTable(diagram)
    exit()
    # Теперь вся диаграмма выходит из одного корня.
    # начинаем избавляться от небинарности. для этого сортируем узлы таблицы по (место в порядке, номер вершины)
    # и идём снизу вверх. если небинарность мы опустили вниз, то можно дальше убирать её в нижнем узле
    # а не заново строить и сортировать таблицу



    # начинаем рекурсивно уводить связи вниз.
    stop_flag = True
    question_leaf = diagram.GetQuestionLeaf()
    while BDDiagram.NonBinaryNodesCount(diagram) > 0:
        nodes = diagram.table_.values()
        print('\nNodes list before sort')
        for node in nodes:
            print("Node", node.vertex_id,
                "var", node.Value(),
                node.node_type,
                "hc:", [(x.vertex_id, x.Value()) for x in node.high_childs],
                "lc:", [(x.vertex_id, x.Value()) for x in node.low_childs])
        nodes = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_, nodes)
        print('\nNodes list after sort')
        for node in nodes:
            print("Node", node.vertex_id,
                "var", node.Value(),
                node.node_type,
                "hc:", [(x.vertex_id, x.Value()) for x in node.high_childs],
                "lc:", [(x.vertex_id, x.Value()) for x in node.low_childs])
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


def ConnectRoots(upper, lower, diagram):
    # в deleted_nodes хранятся узлы, временно удаленные из таблицы, потому что их хэш изменится
    deleted_nodes = set()

    # все корни просто соединяем последовательно двойными связями
    ConnectNodesDouble(None, lower, upper, deleted_nodes, diagram)


def ConnectNodesDouble(host, lower, upper, deleted_nodes, diagram):
    # проверяем количество родителей у узла, в которому приклеиваем
    # если больше 1, то нужно будет его расклеивать
    # когда склеиваем корни такой ситуации вообще не должно происходить
    ungluing_flag = False
    if upper.node_type != DiagramNodeType.QuestionNode:
        if upper.node_type != DiagramNodeType.TrueNode:
            if (len(upper.high_parents) + len(upper.low_parents)) > 1:
                print('Upper have more than 1 parent. Need ungluing.')
                ungluing_flag = True
    if ungluing_flag == True:
        diagram.new_nodes_ += 1
        # тут нам надо расклеить узел на два так, чтобы у одного были все родители, кроме host
        # а у второго только host
        if host is None:
            print('ERROR host is None, but try to ungluing')
        old_upper = upper
        print('Old upper', [old_upper.vertex_id, old_upper.Value(), old_upper])
        upper = UngluingNode(upper, host)
        print('New upper', [upper.vertex_id, upper.Value(), upper])

    # затем, если хост есть, то удаляем связь host и lower
    polarity = 'no'
    if host is not None:
        if lower in host.high_parents:
            host.high_parents.remove(lower)
            if host in lower.high_childs:
                lower.high_childs.remove(host)
            else:
                print('ERROR there is no high link from host to lower')
            polarity = 1
        else:
            host.low_parents.remove(lower)
            if host in lower.low_childs:
                lower.low_childs.remove(host)
            else:
                print('ERROR there is no low link from host to lower')
            if polarity == 'no':
                polarity = 0
            else:
                print('ERROR host have double polarity to lower')

    # если upper и lower с разными переменными, то добавляем upper связь к lower по обеим полярностям
    # тут надо помнить, что если у узла есть 1-ребёнок по какой-то полярности, то по ней мы связи больше не добавляем
    if diagram.GetTrueLeaf() not in upper.high_childs:
        upper.high_childs.append(lower)
        lower.high_parents.append(upper)
    if diagram.GetTrueLeaf() not in upper.low_childs:
        upper.low_childs.append(lower)
        lower.low_parents.append(upper)

    # если upper и lower с одинаковыми переменными,
    # то добавляем ссылки на детей lower к upper'у по обеим полярностям (без рекурсии)
    # после чего, если у lower нет родителей больше (кроме host, ссылку на который мы удалили)
    # то удаляем lower (всех его детей мы передали, но лучше проверить, чтобы у них были другие родители кроме lower)

    # удаляем из таблицы всё от upper (включительно) наверх и добавляем снова с пересчитыванием хэшей и склейкой

    #
    # high_glu = False
    # candidates_to_deletion = set()
    # if diagram.GetTrueLeaf() not in upper.high_childs:
    #     # если нет пути в 1, то проверяем есть ли ребенок с той же переменной
    #     for node in upper.high_childs:
    #         if (node.Value() == lower.Value()) and (node.Value() not in ['?', 'true']):
    #             # вот тут надо передать всех детей ловера апперу в high_childs,
    #             # причем рекурсивно проверять условия дублирования детей
    #             high_glu = True
    #             TransferChilds(lower, upper, node, deleted_nodes, candidates_to_deletion, diagram)
    #             break
    #     else:
    #         DeletingNodesFromTable(upper, diagram, deleted_nodes)
    #         upper.high_childs.append(lower)
    #         lower.high_parents.append(upper)
    # else:
    #     # если есть путь в 1, то ничего не делаем по этой полярности
    #     # ставим что произошло поглощение
    #     high_glu = True
    # # тоже самое для 0-детей
    # low_glu = False
    # if diagram.GetTrueLeaf() not in upper.low_childs:
    #     for node in upper.low_childs:
    #         if (node.Value() == lower.Value()) and (node.Value() not in ['?', 'true']):
    #             low_glu = True
    #             TransferChilds(lower,upper,node,deleted_nodes,candidates_to_deletion,diagram)
    #             break
    #     else:
    #         DeletingNodesFromTable(upper, diagram, deleted_nodes)
    #         upper.low_childs.append(lower)
    #         lower.low_parents.append(upper)
    # else:
    #     low_glu = True
    # if high_glu == True and low_glu == True:
    #     # нужно удалить сам узел, сперва проверив, что у него нет родителей и удалив его из родителей его детей,
    #     # затем рекурсивно првоерить детей на то, что если родителей больше нет, то удаляем и эти узлы и тд
    #     RecursiveDeletionNodesFromDiagram(lower,diagram)

def TransferChilds(from_node,upper,to_node,deleted_nodes,candidates_to_deletion,diagram):
    copy_flag = False
    print('\nTransferChilds')
    print('Upper node', [upper.vertex_id, upper.Value()])
    print('Upper high_childs:', [[x.vertex_id, x.Value()] for x in upper.high_childs])
    print('Upper low_childs:', [[x.vertex_id, x.Value()] for x in upper.low_childs])
    print('Transfer childs from node', [from_node.vertex_id, from_node.Value(), from_node])
    print('to node', [to_node.vertex_id, to_node.Value(), from_node])
    if from_node.node_type == DiagramNodeType.TrueNode:
        print('Wtf, from_node is TrueNode', from_node.vertex_id)
    elif from_node.node_type == DiagramNodeType.QuestionNode:
        print('Wtf, from_node is QuestionNode', from_node.vertex_id)
    if to_node.node_type == DiagramNodeType.TrueNode:
        print('Wtf, to_node is TrueNode', to_node.vertex_id)
    elif to_node.node_type == DiagramNodeType.QuestionNode:
        print('Wtf, to_node is QuestionNode', to_node.vertex_id)
    # if to_node.node_type!=DiagramNodeType.QuestionNode:
    #     if to_node.node_type!=DiagramNodeType.TrueNode:
    #         for parent in to_node.high_parents + to_node.low_parents:
    #             if parent is not upper:
    #                 print('To_node have more than 1 parent. Need ungluing.')
    #                 copy_flag = True
    #                 break
    # if copy_flag == True:
    #     diagram.new_nodes_ += 1
    #     # тут нам надо расклеить узел на два так, чтобы у одного были все родители, кроме upper
    #     # а у второго только upper
    #     new_node = UngluingNode(to_node, upper)
    #     print('New to_node', [to_node.vertex_id, to_node.Value(), to_node])
    # else:
    #     new_node = to_node

    if diagram.GetTrueLeaf() not in to_node.high_childs:
        for from_child in from_node.high_childs:
            for to_child in to_node.high_childs:
                if (from_child.Value() == to_child.Value()) and (from_child.Value() not in ['?', 'true']):
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
                if (from_child.Value() == to_child.Value()) and (from_child.Value() not in ['?', 'true']):
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


def UngluingNode(original_node, upper):
    # сперва создаем узел с тем же типом, той же переменной и теми же детьми
    new_node = DiagramNode(original_node.node_type, original_node.var_id, original_node.high_childs,
                           original_node.low_childs)

    # затем убираем upper из родителей original_node
    # и удаляем ссылку из upper на original_node
    polarity = 'no'
    if upper in original_node.high_parents:
        original_node.high_parents.remove(upper)
        if original_node in upper.high_childs:
            upper.high_childs.remove(original_node)
        else:
            print('ERROR ungluing node 1 high')
        polarity = 1
    else:
        original_node.low_parents.remove(upper)
        if original_node in upper.low_childs:
            upper.low_childs.remove(original_node)
        else:
            print('ERROR ungluing node 1 low')
        if polarity == 'no':
            polarity = 0
        else:
            print('ERROR ungluing node double polarity')

    # работаем с new_node. добавляем ему upper в родители по нужной полярности
    # а upper'у добавляем new_node в дети по той же полярности
    if polarity == 1:
        new_node.high_parents.append(upper)
        upper.high_childs.append(new_node)
    elif polarity == 0:
        new_node.low_parents.append(upper)
        upper.low_childs.append(new_node)
    else:
        print('ERROR ungluing node no polarity')

    # а также добавляем всем детям оригинального узла new_node в родители
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

def DrawDiagram(diagram):
    G = GraphVisualization()
    for node in diagram.table_.values():
        nodename = str(node.vertex_id) + ' ' + str(node.Value())
        for highchild in node.high_childs:
            childname = str(highchild.vertex_id) + ' ' + str(highchild.Value())
            G.addHighEdge(nodename, childname)
        for lowchild in node.low_childs:
            childname = str(lowchild.vertex_id) + ' ' + str(lowchild.Value())
            G.addLowEdge(nodename, childname)
    G.visualize()