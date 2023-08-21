from Pathfinder import *
import pysat
from pysat.solvers import MapleChrono
from pysat.formula import CNF
from Draw import *

from Types import DiagramNode
import queue

class BDDiagram:
    new_nodes_ = 0
    deleted_nodes_ = 0
    #nonbinary_queue = queue.LifoQueue()
    nonbinary_queue = []
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
        #CleaningDiagram(self)
        try:
            question_leaf = self.GetQuestionLeaf()
            #print(question_leaf.Value(), [x.Value() for x in question_leaf.high_parents],[x.Value() for x in question_leaf.low_parents])
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

    # def PrintCurrentQueue(self):
    #     for node_pol in list(self.nonbinary_queue):
    #         print("\nNode", node_pol[0].vertex_id,
    #               "var", node_pol[0].Value(),
    #               node_pol[0].node_type,
    #               "hc:", [(x.vertex_id, x.Value()) for x in node_pol[0].high_childs],
    #               "lc:", [(x.vertex_id, x.Value()) for x in node_pol[0].low_childs],
    #               'polarity', node_pol[1],
    #               '\n')

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
    #sorted_roots2_ = DisjunctiveDiagramsBuilder.LitLessSortNodeswrtOrderAndVertex(diagram.order_, diagram.roots_)
    print('Sorted Roots', [(x.vertex_id, x.var_id) for x in sorted_roots_])
    #print('\nTable before roots gluing:')
    #BDDiagram.PrintCurrentTable(diagram)
    main_root = sorted_roots_[-1]
    for i in range(len(sorted_roots_)-1):
        print('Connect root', str(sorted_roots_[i].vertex_id) + '_' + str(sorted_roots_[i].var_id), ' to root', str(sorted_roots_[i+1].vertex_id) + '_' + str(sorted_roots_[i+1].var_id))
        # присоединяем нижний корень к верхнему по двум полярностям
        ConnectRoots(sorted_roots_[i+1], sorted_roots_[i],diagram)
    # теперь diagram.roots_ неправильная, потому что хэши поменялись (бтв, в table всё обновлено), но это и неважно
    #print('Roots', [(x.vertex_id, x.var_id, x.node_type) for x in diagram.roots_])
    diagram.main_root_ = main_root
    print('Main root number:', main_root.vertex_id,'; variable:',main_root.var_id)
    print('Number of nonbinary links in diagram after roots gluing is', BDDiagram.NonBinaryLinkCount(diagram))
    print('Number of nonbinary nodes in diagram after roots gluing is', BDDiagram.NonBinaryNodesCount(diagram))
    #print('\nTable after roots gluing:')
    #BDDiagram.PrintCurrentTable(diagram)
    #exit()

    # Теперь вся диаграмма выходит из одного корня.
    # начинаем избавляться от небинарности. для этого сортируем узлы таблицы по (место в порядке, номер вершины)
    # и идём снизу вверх. если небинарность мы опустили вниз, то можно дальше убирать её в нижнем узле
    # а не заново строить и сортировать таблицу
    print('Start remove nonbinary links.')
    while BDDiagram.NonBinaryNodesCount(diagram) > 0:
        print('\n\nCurrent number of nonbinary nodes in diagram', BDDiagram.NonBinaryNodesCount(diagram))
        sorted_nodes = DisjunctiveDiagramsBuilder.LitLessSortNodeswrtOrderAndVertex(diagram.order_, diagram.table_.values())
        print('Number of nodes', len(sorted_nodes))
        first_nonbinary_node, polarity = FindFirstNonbinaryNode(sorted_nodes)
        print('First nonbinary node', first_nonbinary_node.vertex_id, 'var', first_nonbinary_node.var_id)
        # BDDiagram.nonbinary_queue.put([first_nonbinary_node, polarity])
        BDDiagram.nonbinary_queue.append([first_nonbinary_node, polarity])
        # while not BDDiagram.nonbinary_queue.empty():
        while BDDiagram.nonbinary_queue:
            # print('\nCurrent size of queue', BDDiagram.nonbinary_queue.qsize())
            # host = BDDiagram.nonbinary_queue.get()
            print('\nCurrent size of queue', len(BDDiagram.nonbinary_queue))
            host = BDDiagram.nonbinary_queue.pop()
            print('Current host:', end=' ')
            host[0].PrintNode()
            print('Polarity:', host[1])
            # BDDiagram.PrintCurrentQueue(diagram)
            RemoveNonbinaryLink(host[0], host[1], diagram)

    print('\nTable after BDD transformation:')
    BDDiagram.PrintCurrentTable(diagram)


def RemoveNonbinaryLink(host, polarity, diagram):
    if (polarity == 1 and len(host.high_childs) > 1) or (polarity == 0 and len(host.low_childs) > 1):
        sorted_childs = DisjunctiveDiagramsBuilder.LitLessSortNodeswrtOrderAndVertex(diagram.order_,
                                                                                     (host.high_childs if polarity == 1
                                                                                      else host.low_childs))
        lower = sorted_childs[0]
        print('Current lower:', end=' ')
        lower.PrintNode()
        upper = sorted_childs[1]
        print('Current upper:', end=' ')
        upper.PrintNode()
        upper_and_polarity = ConnectNodesDouble(host, polarity, lower, upper, diagram)
        if upper_and_polarity[1] == 'both':
            # если через очередь, то append заменяем на put
            BDDiagram.nonbinary_queue.append([upper_and_polarity[0], 0])
            BDDiagram.nonbinary_queue.append([upper_and_polarity[0], 1])
        elif upper_and_polarity[1] != 'no':
            BDDiagram.nonbinary_queue.append(upper_and_polarity)


def FindFirstNonbinaryNode(sorted_nodes):
    for node in sorted_nodes:
        if len(node.high_childs) > 1:
            return node, 1
        elif len(node.low_childs) > 1:
            return node, 0


def ConnectRoots(upper, lower, diagram):
    # все корни просто соединяем последовательно двойными связями
    lower.node_type = DiagramNodeType.InternalNode
    upper_and_polarity = ConnectNodesDouble(None, None, lower, upper, diagram)


def ConnectNodesDouble(host, polarity, lower, upper, diagram):
    # проверяем количество родителей у узла, в которому приклеиваем
    # если больше 1, то нужно будет его расклеивать
    # когда склеиваем корни такой ситуации вообще не должно происходить
    old_upper = upper
    upper = CheckNodeForUngluing(diagram, upper, host, polarity)

    # удаляем из таблицы всё от upper (включительно) наверх и добавляем снова с пересчитыванием хэшей и склейкой
    nodes_with_changed_hash = set()
    if host is not None:
        DisjunctiveDiagramsBuilder.DeletingNodesFromTable(upper, diagram, nodes_with_changed_hash)
    else:
        del diagram.table_[upper.hash_key]


    print('\nАfter DeletingNodesFromTable New node')
    upper.PrintNode()
    print('New node highchilds')
    for child in upper.high_childs:
        child.PrintNode()
    print('New node lowchilds')
    for child in upper.low_childs:
        child.PrintNode()
    print()

    # затем, если хост есть, то удаляем связь host и lower
    if host is not None:
        RemoveLinkFromHostToLower(diagram, host, lower, polarity)

    print('\nАfter RemoveLinkFromHostToLower New node')
    upper.PrintNode()
    print('New node highchilds')
    for child in upper.high_childs:
        child.PrintNode()
    print('New node lowchilds')
    for child in upper.low_childs:
        child.PrintNode()
    print()

    if upper.Value() != lower.Value():
        # если upper и lower с разными переменными, то добавляем upper связь к lower по обеим полярностям
        # тут надо помнить, что если у узла есть 1-ребёнок по какой-то полярности,
        # то по ней мы связи больше не добавляем
        DoubleConnectLowerToUpper(diagram, upper, lower)
    else:
        # если upper и lower с одинаковыми переменными,
        # то добавляем ссылки на детей lower к upper'у по обеим полярностям (без рекурсии)
        # при этом если у lower есть 1-вершина в детях, то она поглощает детей аппера.
        TranferChildsFromLowerToUpper(diagram, upper, lower)

    print('\nАfter connect lower to upper New node')
    upper.PrintNode()
    print('New node highchilds')
    for child in upper.high_childs:
        child.PrintNode()
    print('New node lowchilds')
    for child in upper.low_childs:
        child.PrintNode()
    print()

    # после чего, если у lower нет родителей больше (кроме host, ссылку на который мы удалили)
    # то удаляем lower (всех его детей мы передали, но лучше проверить)
    if (len(lower.high_parents) + len(lower.low_parents)) == 0:
        print('Lower without parents. Delete it.')
        DeleteNodeWithoutParents(lower, nodes_with_changed_hash, diagram)

    print('\nАfter DeleteNodeWithoutParents New node')
    upper.PrintNode()
    print('New node highchilds')
    for child in upper.high_childs:
        child.PrintNode()
    print('New node lowchilds')
    for child in upper.low_childs:
        child.PrintNode()
    print()

    # тут мы проверяем, что если у аппера после наших действий есть небинарность такая
    # что одна связь идёт в внутреннюю вершину, а другая в ?-вершину
    # то связь в ?-вершину мы просто удаляем
    # UPD такого быть больше не должно в принципе, так что комментим
    # CheckNonbinaryWithQuestionNode(upper, diagram)
    # тут мы проверяем, что если у аппера после наших действий есть небинарность такая
    # что одна связь идёт в внутреннюю вершину, а другая в 1-вершину
    # то все связи, кроме той, что ведёт в 1-вершину, мы удаляем
    # UPD такого быть больше не должно в принципе, так что комментим
    # CheckNonbinaryWithTrueNode(upper, diagram)

    # возвращаем всё в таблицу с проверкой на склейку
    if host is not None:
        upper = GluingNodes(upper, nodes_with_changed_hash, diagram)
    else:
        upper.HashKey()
        diagram.table_[upper.hash_key] = upper

    print('\nАfter GluingNodes ungluing New node')
    upper.PrintNode()
    print('New node highchilds')
    for child in upper.high_childs:
        child.PrintNode()
    print('New node lowchilds')
    for child in upper.low_childs:
        child.PrintNode()
    print()

    # проверяем небинарность upper
    if len(upper.high_childs) > 1 and len(upper.low_childs) > 1:
        upper_nonbinary_polarity = 'both'
    elif len(upper.high_childs) > 1:
        upper_nonbinary_polarity = 1
    elif len(upper.low_childs) > 1:
        upper_nonbinary_polarity = 0
    else:
        upper_nonbinary_polarity = 'no'

    return [upper, upper_nonbinary_polarity]


def RemoveLinkFromHostToLower(diagram, host, lower, polarity):
    print('RemoveLinkFromHostToLower before Host:', end=' ')
    host.PrintNode()
    print('RemoveLinkFromHostToLower before Lower:', end=' ')
    lower.PrintNode()
    if polarity == 1:
        host_len_childs_before = len(host.high_childs)
        lower_len_parents_before = len(lower.high_parents)
        if lower in host.high_childs:
            host.high_childs = [x for x in host.high_childs if x is not lower]
            if host in lower.high_parents:
                lower.high_parents = [x for x in lower.high_parents if x is not host]
            else:
                print('ERROR there is no high_parent link from lower to host')
                exit()
        else:
            print('ERROR polarity is 1, but there is no high_child link from host to lower')
            exit()
        # if host_len_childs_before-len(host.high_childs) != 1:
        #     print('ERROR removed more than 1 link from host high childs')
        #     exit()
        # if lower_len_parents_before-len(lower.high_parents) != 1:
        #     print('ERROR removed more than 1 link from lower high parents')
        #     exit()
    elif polarity == 0:
        if lower in host.low_childs:
            host.low_childs = [x for x in host.low_childs if x is not lower]
            if host in lower.low_parents:
                lower.low_parents = [x for x in lower.low_parents if x is not host]
            else:
                print('ERROR there is no low_parent link from lower to host')
                exit()
        else:
            print('ERROR polarity is 0, but there is no low_child link from host to lower')
            exit()
    else:
        print('ERROR Host is not None, but polarity not 0 or 1.')
        exit()
    # print('RemoveLinkFromHostToLower after Host:', end=' ')
    # host.PrintNode()
    # print('RemoveLinkFromHostToLower after Lower:', end=' ')
    # lower.PrintNode()


def CheckNodeForUngluing(diagram, upper, host, polarity):
    if upper.node_type != DiagramNodeType.QuestionNode:
        if upper.node_type != DiagramNodeType.TrueNode:
            if (len(upper.high_parents) + len(upper.low_parents)) > 1:
                print('Upper have more than 1 parent. Need ungluing.')
                diagram.new_nodes_ += 1
                # тут нам надо расклеить узел на два так, чтобы у одного были все родители, кроме host
                # а у второго только host
                if host is None:
                    print('ERROR host is None, but try to ungluing')
                    exit()
                print('Old upper')
                upper.PrintNode()
                new_upper = UngluingNode(upper, host, polarity)
                print('New upper')
                new_upper.PrintNode()
                return new_upper
            else:
                return upper
        else:
            print('\nHost:', end=' ')
            host.PrintNodeWithoutParents()
            print('Upper:', end=' ')
            upper.PrintNodeWithoutParents()
            raise Exception('ERROR Upper is a TrueNode')
    else:
        print('\nHost:', end=' ')
        host.PrintNodeWithoutParents()
        print('Upper:', end=' ')
        upper.PrintNodeWithoutParents()
        raise Exception('ERROR Upper is a QuestionNode')

def DoubleConnectLowerToUpper(diagram, upper, lower):
    true_leaf = diagram.GetTrueLeaf()
    question_leaf = diagram.GetQuestionLeaf()
    # все проверки можно переделать под проверки ссылок, а не "not in"
    # к примеру добавить метод NotIn в класс узлов, который бы проверял как раз ссылки
    # хотя вообще это ничего поменять не должно, потому что тут расклейка не влияет
    if true_leaf not in upper.high_childs:
        if lower not in upper.high_childs:
            upper.high_childs.append(lower)
            upper.high_childs = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_, upper.high_childs)
        if upper not in lower.high_parents:
            lower.high_parents.append(upper)
            lower.high_parents = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_, lower.high_parents)
        if question_leaf in upper.high_childs and len(upper.high_childs) > 1:
            upper.high_childs.remove(question_leaf)
            question_leaf.high_parents = [x for x in question_leaf.high_parents if x is not upper]
    if true_leaf not in upper.low_childs:
        if lower not in upper.low_childs:
            upper.low_childs.append(lower)
            upper.low_childs = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_, upper.low_childs)
        if upper not in lower.low_parents:
            lower.low_parents.append(upper)
            lower.low_parents = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_, lower.low_parents)
        if question_leaf in upper.low_childs and len(upper.low_childs) > 1:
            upper.low_childs.remove(question_leaf)
            question_leaf.low_parents = [x for x in question_leaf.low_parents if x is not upper]

def TranferChildsFromLowerToUpper(diagram, upper, lower):
    if diagram.GetTrueLeaf() not in upper.high_childs:
        if diagram.GetTrueLeaf() in lower.high_childs:
            SetTrueChild(diagram, upper, 1)
        else:
            for high_child in lower.high_childs:
                if high_child not in upper.high_childs:
                    upper.high_childs.append(high_child)
                    high_child.high_parents.append(upper)
                    high_child.high_parents = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_,
                                                                                          high_child.high_parents)
            upper.high_childs = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_, upper.high_childs)
    if diagram.GetTrueLeaf() not in upper.low_childs:
        if diagram.GetTrueLeaf() in lower.low_childs:
            SetTrueChild(diagram, upper, 0)
        else:
            for low_child in lower.low_childs:
                if low_child not in upper.low_childs:
                    upper.low_childs.append(low_child)
                    low_child.low_parents.append(upper)
                    low_child.low_parents = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_,
                                                                                        low_child.low_parents)
            upper.low_childs = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_, upper.low_childs)


def CheckNonbinaryWithTrueNode(node, diagram):
    print('\nCheckNonbinaryWithTrueNode')
    node.PrintNodeWithoutParents()
    true_leaf = diagram.GetTrueLeaf()
    if len(node.high_childs) > 1 and true_leaf in node.high_childs:
        for child in node.high_childs:
            if child is not true_leaf:
                child.high_parents = [x for x in child.high_parents if x is not node]
        node.high_childs = [true_leaf]
    if len(node.low_childs) > 1 and true_leaf in node.low_childs:
        for child in node.low_childs:
            if child is not true_leaf:
                child.low_parents = [x for x in child.low_parents if x is not node]
        node.low_childs = [true_leaf]

def CheckNonbinaryWithQuestionNode(node, diagram):
    print('\nCheckNonbinaryWithQuestionNode')
    node.PrintNodeWithoutParents()
    question_leaf = diagram.GetQuestionLeaf()
    if len(node.high_childs) > 1 and question_leaf in node.high_childs:
        node.high_childs.remove(question_leaf)
        if node in question_leaf.high_parents:
            question_leaf.high_parents = [x for x in question_leaf.high_parents if x is not node]
        else:
            print('ERROR exist high_child link "node->?", but not exist reversed parent link')
            exit()
    if len(node.low_childs) > 1 and question_leaf in node.low_childs:
        node.low_childs.remove(question_leaf)
        if node in question_leaf.low_parents:
            question_leaf.low_parents = [x for x in question_leaf.low_parents if x is not node]
        else:
            print('ERROR exist low_child link "node->?", but not exist reversed parent link')
            exit()


def SetTrueChild(diagram, node, polarity):
    if polarity == 1:
        for child in node.high_childs:
            child.high_parents = [x for x in child.high_parents if x is not node]
        node.high_childs = [diagram.GetTrueLeaf()]
    elif polarity == 0:
        for child in node.low_childs:
            child.low_parents = [x for x in child.low_parents if x is not node]
        node.low_childs = [diagram.GetTrueLeaf()]


def UngluingNode(original_node, host, polarity):
    # сперва создаем узел с тем же типом, той же переменной и теми же детьми
    new_node = DiagramNode(original_node.node_type, original_node.var_id, original_node.high_childs,
                           original_node.low_childs)
    # и добавляем его в родители детей
    AddNodeToParentsOfChilds(new_node)
    if polarity == None:
        print('ERROR Polarity None when ungluing node')
        exit()
    # затем убираем upper из родителей original_node
    # и удаляем ссылку из upper на original_node
    if polarity == 1:
        if host in original_node.high_parents:
            original_node.high_parents = [x for x in original_node.high_parents if x is not host]
            if original_node in host.high_childs:
                host.high_childs = [x for x in host.high_childs if x is not original_node]
            else:
                print('ERROR ungluing node 1 high (no old upper in host highchilds)')
                exit()
        else:
            print('Old upper high parents:', [(x.vertex_id, x.var_id) for x in original_node.high_parents])
            print('Host', end=' ')
            host.PrintNodeWithoutParents()
            print('ERROR ungluing node 2 high (no host in old upper highparents)')
            exit()
    elif polarity == 0:
        if host in original_node.low_parents:
            original_node.low_parents = [x for x in original_node.low_parents if x is not host]
            if original_node in host.low_childs:
                host.low_childs = [x for x in host.low_childs if x is not original_node]
            else:
                print('ERROR ungluing node 1 low')
                exit()
        else:
            print('ERROR ungluing node 2 low')
            exit()

    # работаем с new_node. добавляем ему host в родители по нужной полярности
    # а host'у добавляем new_node в дети по той же полярности
    if polarity == 1:
        new_node.high_parents.append(host)
        host.high_childs.append(new_node)
    elif polarity == 0:
        new_node.low_parents.append(host)
        host.low_childs.append(new_node)
    else:
        print('ERROR ungluing node no polarity')
        exit()
    # проверка чтобы new_node был где надо
    print('\nRight after ungluing New node')
    new_node.PrintNode()
    print('New node highchilds')
    for child in new_node.high_childs:
        child.PrintNode()
    print('New node lowchilds')
    for child in new_node.low_childs:
        child.PrintNode()
    print()
    return new_node


def DeleteNodeWithoutParents(node, nodes_with_changed_hash, diagram):
    # при удалении узла мы удаляем ссылки на него из детей
    print('Delete node without parents')
    node.PrintNode()
    print('Low childs:')
    for low_child in node.low_childs:
        print('Low child before:', end=' ')
        low_child.PrintNode()
        low_child.low_parents = [x for x in low_child.low_parents if x is not node]
        print('Low child after:', end=' ')
        low_child.PrintNode()
    print('High childs:')
    for high_child in node.high_childs:
        print('High child before:', end=' ')
        high_child.PrintNode()
        high_child.high_parents = [x for x in high_child.high_parents if x is not node]
        print('High child after:', end=' ')
        high_child.PrintNode()
    if node in nodes_with_changed_hash:
        # хотя он, по идее, обязательно тут должен быть, так что проверка не особо то и нужна, но пусть будет
        nodes_with_changed_hash.remove(node)
    del node


def AddNodeToParentsOfChilds(new_node):
    # эта функция нужна при создании новых узлов вне процедуры построения DJD,
    # так как в __init__ нет работы с родителями
    for child in new_node.high_childs:
        child.high_parents.append(new_node)
    for child in new_node.low_childs:
        child.low_parents.append(new_node)


def GluingNodes(upper, nodes_with_changed_hash, diagram):
    nodes_with_changed_hash = DisjunctiveDiagramsBuilder.LitLessSortNodeswrtOrderAndVertex(diagram.order_,
                                                                                           nodes_with_changed_hash)
    new_upper = upper
    for node in nodes_with_changed_hash:
        node.HashKey()
        if node.hash_key in diagram.table_ and diagram.table_[node.hash_key] is not node:
            node_to_which_glue = diagram.table_[node.hash_key]
            if node is node_to_which_glue:
                print('ERROR')
            print('Glued node', end=' ')
            node.PrintNode()
            print('with node', end=' ')
            node_to_which_glue.PrintNode()
            if node is upper:
                new_upper = node_to_which_glue
            for node_pol in diagram.nonbinary_queue:
                if node_pol[0] is node:
                    node_pol[0] = node_to_which_glue
            GluingNode(node, node_to_which_glue)
            del node
            diagram.deleted_nodes_ += 1
        else:
            diagram.table_[node.hash_key] = node
    return new_upper

def GluingNode(node, node_to_which_glue):
    # заменяем ссылки в родителях
    ReplaceParentsLinksToNode(node, node_to_which_glue)
    # Удаляем ссылки потомков узла на него
    DeleteChildsLinksToNode(node)


def ReplaceParentsLinksToNode(node,node_to_which_glue):
    for parent in node.high_parents:
        parent.high_childs = [x for x in parent.high_childs if x is not node and x is not node_to_which_glue]
        parent.high_childs.append(node_to_which_glue)
        for tmpnode in node_to_which_glue.high_parents:
            if tmpnode is parent:
                break
        else:
            #print('add as highparent ', (parent.Value(), parent), 'to node', (it_node.Value(), it_node))
            node_to_which_glue.high_parents.append(parent)
    for parent in node.low_parents:
        parent.low_childs = [x for x in parent.low_childs if x is not node and x is not node_to_which_glue]
        parent.low_childs.append(node_to_which_glue)
        for tmpnode in node_to_which_glue.low_parents:
            if tmpnode is parent:
                break
        else:
            node_to_which_glue.low_parents.append(parent)
            #print('add as lowparent ', (parent.Value(), parent), 'to node', (it_node.Value(), it_node))


def DeleteChildsLinksToNode(node):
    for child in node.high_childs:
        child.high_parents = [x for x in child.high_parents if x is not node]
    for child in node.low_childs:
        child.low_parents = [x for x in child.low_parents if x is not node]




# def TransferChilds(from_node,upper,to_node,deleted_nodes,candidates_to_deletion,diagram):
#     copy_flag = False
#     print('\nTransferChilds')
#     print('Upper node', [upper.vertex_id, upper.Value()])
#     print('Upper high_childs:', [[x.vertex_id, x.Value()] for x in upper.high_childs])
#     print('Upper low_childs:', [[x.vertex_id, x.Value()] for x in upper.low_childs])
#     print('Transfer childs from node', [from_node.vertex_id, from_node.Value(), from_node])
#     print('to node', [to_node.vertex_id, to_node.Value(), from_node])
#     if from_node.node_type == DiagramNodeType.TrueNode:
#         print('Wtf, from_node is TrueNode', from_node.vertex_id)
#     elif from_node.node_type == DiagramNodeType.QuestionNode:
#         print('Wtf, from_node is QuestionNode', from_node.vertex_id)
#     if to_node.node_type == DiagramNodeType.TrueNode:
#         print('Wtf, to_node is TrueNode', to_node.vertex_id)
#     elif to_node.node_type == DiagramNodeType.QuestionNode:
#         print('Wtf, to_node is QuestionNode', to_node.vertex_id)
#     # if to_node.node_type!=DiagramNodeType.QuestionNode:
#     #     if to_node.node_type!=DiagramNodeType.TrueNode:
#     #         for parent in to_node.high_parents + to_node.low_parents:
#     #             if parent is not upper:
#     #                 print('To_node have more than 1 parent. Need ungluing.')
#     #                 copy_flag = True
#     #                 break
#     # if copy_flag == True:
#     #     diagram.new_nodes_ += 1
#     #     # тут нам надо расклеить узел на два так, чтобы у одного были все родители, кроме upper
#     #     # а у второго только upper
#     #     new_node = UngluingNode(to_node, upper)
#     #     print('New to_node', [to_node.vertex_id, to_node.Value(), to_node])
#     # else:
#     #     new_node = to_node
#
#     if diagram.GetTrueLeaf() not in to_node.high_childs:
#         for from_child in from_node.high_childs:
#             for to_child in to_node.high_childs:
#                 if (from_child.Value() == to_child.Value()) and (from_child.Value() not in ['?', 'true']):
#                     candidates_to_deletion.add(from_child)
#                     TransferChilds(from_child,to_node,to_child,deleted_nodes,candidates_to_deletion,diagram)
#                     break
#             else:
#                 to_node.high_childs.append(from_child)
#                 from_child.high_parents.append(to_node)
#     else:
#         candidates_to_deletion.update(from_node.high_childs)
#         # тут нужно какимто образом удалить потомков, если они больше не нужны нигде (нужна вот эта проверка на нужность)
#     if diagram.GetTrueLeaf() not in to_node.low_childs:
#         for from_child in from_node.low_childs:
#             for to_child in to_node.low_childs:
#                 if (from_child.Value() == to_child.Value()) and (from_child.Value() not in ['?', 'true']):
#                     candidates_to_deletion.add(from_child)
#                     TransferChilds(from_child,to_node, to_child, deleted_nodes,candidates_to_deletion,diagram)
#                     break
#             else:
#                 to_node.low_childs.append(from_child)
#                 from_child.low_parents.append(to_node)
#     else:
#         candidates_to_deletion.update(from_node.low_childs)
#         # тут нужно какимто образом удалить потомков, если они больше не нужны нигде (нужна вот эта проверка на нужность)
#     if copy_flag == True:
#         deleted_nodes = set([x for x in deleted_nodes if x is not to_node])
#         to_node.HashKey()
#         deleted_nodes.add(to_node)
#         deleted_nodes.add(new_node)

# def RecursiveDeletionNodesFromDiagram(lower,diagram):
#     if lower.node_type is not DiagramNodeType.QuestionNode \
#             and lower.node_type is not DiagramNodeType.TrueNode\
#             and len(lower.high_parents) == 0\
#             and len(lower.low_parents) == 0:
#         for child in lower.high_childs:
#             child.high_parents = [x for x in child.high_parents if x is not lower]
#             RecursiveDeletionNodesFromDiagram(child,diagram)
#         for child in lower.low_childs:
#             child.low_parents = [x for x in child.low_parents if x is not lower]
#             RecursiveDeletionNodesFromDiagram(child,diagram)
#         if lower.hash_key in diagram.table_:
#             #print('del from table', (lower.vertex_id, lower.Value()))
#             del diagram.table_[lower.hash_key]
#             #if lower.hash_key in diagram.table_:
#                 #print('ERROR NO DEL')
#         print('del node', (lower.vertex_id, lower.Value()))
#         diagram.deleted_nodes_ += 1
#         del lower
#
#
# def FindNonbinaryNodesFromTerminal(diagram:DisjunctiveDiagram, current_node):
#     find_flag = False
#     for node in current_node.high_parents + current_node.low_parents:
#         if len(node.high_childs) > 1:
#             """
#             print('Find nonbinary node:', (node.vertex_id, node.Value()), 'hc', "hc:", [(x.vertex_id, x.Value()) for x in
#                                                                   node.high_childs], "lc:", [(x.vertex_id, x.Value())
#                                                                                              for x in node.low_childs])
#             """
#             GettingRidOfNonbinary(diagram, node, 1)
#             find_flag = True
#             break
#         elif len(node.low_childs) > 1:
#             """
#             print('Find nonbinary node:', (node.vertex_id, node.Value()), 'lc', "hc:", [(x.vertex_id, x.Value()) for x in
#                                                                   node.high_childs], "lc:", [(x.vertex_id, x.Value())
#                                                                                              for x in node.low_childs])
#             """
#             GettingRidOfNonbinary(diagram, node, 0)
#             find_flag = True
#             break
#         else:
#             find_flag = FindNonbinaryNodesFromTerminal(diagram, node)
#             if find_flag == True:
#                 return True
#     if find_flag == True:
#         return True
#     return False

# def GettingRidOfNonbinary(diagram:DisjunctiveDiagram, node, polarity):
#     if polarity == 1:
#         childs = node.high_childs
#     else:
#         childs = node.low_childs
#     deleted_nodes = set()
#     upper_node, lower_node = FindUpperAndLowerChilds(childs, diagram.order_)
#     print('Upper node:', (upper_node.vertex_id, upper_node.Value()),'Lower node:', (lower_node.vertex_id, lower_node.Value()))
#     DeletingNodesFromTable(upper_node, diagram, deleted_nodes)
#     DeleteLinkFromNode(lower_node, node, polarity)
#     if lower_node is not diagram.GetQuestionLeaf() \
#             and upper_node is not diagram.GetTrueLeaf() \
#             and upper_node is not diagram.GetQuestionLeaf():
#         ConnectNodesDouble(lower_node, upper_node, deleted_nodes, diagram)
#     elif upper_node is diagram.GetTrueLeaf():
#         RecursiveDeletionNodesFromDiagram(lower_node,diagram)
#     deleted_nodes = LitLessSortNodes(deleted_nodes, diagram.order_)
#     GluingNodes(deleted_nodes, diagram)
#
# # Рекурсивное удаление узлов из таблицы от node наверх
# def DeletingNodesFromTable(node, diagram, deleted_nodes):
#     deleted_nodes.add(node)
#     if node.hash_key in diagram.table_ and node is not diagram.GetTrueLeaf() and node is not diagram.GetQuestionLeaf():
#         del diagram.table_[node.hash_key]
#         for parent in set(node.high_parents+node.low_parents):
#             DeletingNodesFromTable(parent, diagram, deleted_nodes)
#     #for parent in node.low_parents:
#         #DeletingNodesFromTable(parent, diagram, deleted_nodes)
#
# #находим у небинарного узла верхнего и нижнего потомка по небинарной полярности
# def FindUpperAndLowerChilds(childs, order):
#     sorted_childs = LitLessSortNodes(set(childs),order)
#     lower = sorted_childs[0]
#     upper = sorted_childs[1]
#     return upper, lower
#
#
# #Сортировка множества узлов w.r.t. order
# def LitLessSortNodes(nodes:set,order:list):
#     nodes = list(nodes)
#     sorted_nodes = [node for x in order for node in nodes if node.Value() == x]
#     return sorted_nodes
#
# #удаляем связь между небинарным узлом и нижним потомком по небинарной полярности
# def DeleteLinkFromNode(lower_node, node, polarity):
#     if polarity == 1:
#         node.high_childs = [x for x in node.high_childs if x is not lower_node]
#         lower_node.high_parents = [x for x in lower_node.high_parents if x is not node]
#     else:
#         node.low_childs = [x for x in node.low_childs if x is not lower_node]
#         lower_node.low_parents = [x for x in lower_node.low_parents if x is not node]
#
# def CreateLinkBetweenLowerToUpper(lower_node, upper_node):
#     if upper_node not in lower_node.high_parents:
#         lower_node.high_parents.append(upper_node)
#     if upper_node not in lower_node.low_parents:
#         lower_node.low_parents.append(upper_node)
#     if lower_node not in upper_node.high_childs:
#         upper_node.high_childs.append(lower_node)
#     if lower_node not in upper_node.low_childs:
#         upper_node.low_childs.append(lower_node)
#
# def GluingNodes(deleted_nodes, diagram):
#     deleted_nodes = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_, deleted_nodes)
#     for node in deleted_nodes:
#         node.HashKey()
#         if node.hash_key in diagram.table_ and diagram.table_[node.hash_key] is not node:
#             it_node = diagram.table_[node.hash_key]
#             if node is it_node:
#                 print('ERROR')
#             #print('Glued node',(node.Value(), node),'with node',(it_node.Value(),it_node))
#             GluingNode(node,it_node)
#             diagram.deleted_nodes_ += 1
#             print('del glu node',(node.Value(), node))
#             del node
#         else:
#             diagram.table_[node.hash_key] = node
#
# def GluingNode(node,it_node):
#     # заменяем ссылки в родителях
#     ReplaceParentsLinksToNode(node,it_node)
#     # Удаляем ссылки потомков узла на него
#     DeleteChildsLinksToNode(node)
#     # Заменяем узел в node_paths
#     #ReplaceNodeInNodePaths(node,it_node,node_paths)
#
# def ReplaceParentsLinksToNode(node,it_node):
#     for parent in node.high_parents:
#         parent.high_childs = [x for x in parent.high_childs if x is not node and x is not it_node]
#         parent.high_childs.append(it_node)
#         for tmpnode in it_node.high_parents:
#             if tmpnode is parent:
#                 break
#         else:
#             #print('add as highparent ', (parent.Value(), parent), 'to node', (it_node.Value(), it_node))
#             it_node.high_parents.append(parent)
#     for parent in node.low_parents:
#         parent.low_childs = [x for x in parent.low_childs if x is not node and x is not it_node]
#         parent.low_childs.append(it_node)
#         for tmpnode in it_node.low_parents:
#             if tmpnode is parent:
#                 break
#         else:
#             it_node.low_parents.append(parent)
#             #print('add as lowparent ', (parent.Value(), parent), 'to node', (it_node.Value(), it_node))
#
# def DeleteChildsLinksToNode(node):
#     for child in node.high_childs:
#         child.high_parents = [x for x in child.high_parents if x is not node]
#     for child in node.low_childs:
#         child.low_parents = [x for x in child.low_parents if x is not node]
#
#
# def FindNonbinaryNodesFromRoot(diagram:DisjunctiveDiagram, current_node):
#     find_flag = False
#     if len(current_node.high_childs) > 1:
#
#         print('Find nonbinary node:', (current_node.vertex_id, current_node.Value()), 'hc', "hc:", [(x.vertex_id, x.Value()) for x in
#                                                             current_node.high_childs], "lc:", [(x.vertex_id, x.Value())
#                                                                                         for x in current_node.low_childs])
#
#         GettingRidOfNonbinary(diagram, current_node, 1)
#         find_flag = True
#     elif len(current_node.low_childs) > 1:
#
#         print('Find nonbinary node:', (current_node.vertex_id, current_node.Value()), 'lc', "hc:", [(x.vertex_id, x.Value()) for x in
#                                                             current_node.high_childs], "lc:", [(x.vertex_id, x.Value())
#                                                                                         for x in current_node.low_childs])
#
#         GettingRidOfNonbinary(diagram, current_node, 0)
#         find_flag = True
#     if find_flag == True:
#         return True
#     for node in current_node.high_childs + current_node.low_childs:
#         find_flag = FindNonbinaryNodesFromRoot(diagram, node)
#         if find_flag == True:
#             return True
#     return False
#
# def FindNonbinaryNodesInTable(diagram, current_node):
#     find_flag = False
#     if len(current_node.high_childs) > 1:
#         print('')
#         print('Current number of nonbinary links is', BDDiagram.NonBinaryLinkCount(diagram))
#         print('Current number of nonbinary nodes is', BDDiagram.NonBinaryNodesCount(diagram))
#         print('Find nonbinary node:', (current_node.vertex_id, current_node.Value()), 'hc', "hc:", [(x.vertex_id, x.Value()) for x in
#                                                             current_node.high_childs], "lc:", [(x.vertex_id, x.Value())
#                                                                                         for x in current_node.low_childs])
#         GettingRidOfNonbinary(diagram, current_node, 1)
#         find_flag = True
#     elif len(current_node.low_childs) > 1:
#         print('')
#         print('Current number of nonbinary links is', BDDiagram.NonBinaryLinkCount(diagram))
#         print('Current number of nonbinary nodes is', BDDiagram.NonBinaryNodesCount(diagram))
#         print('Find nonbinary node:', (current_node.vertex_id, current_node.Value()), 'lc', "hc:", [(x.vertex_id, x.Value()) for x in
#                                                             current_node.high_childs], "lc:", [(x.vertex_id, x.Value())
#                                                                                         for x in current_node.low_childs])
#         GettingRidOfNonbinary(diagram, current_node, 0)
#         find_flag = True
#     if find_flag == True:
#         return True
#     return False
#
# def CleaningDiagram(diagram):
#     all_nodes = sorted([node for node in diagram.table_.values()], key=lambda x: x.vertex_id)
#     while len(all_nodes) > 0:
#         node = all_nodes[0]
#         all_nodes = all_nodes[1:]
#         print('lenb',len(all_nodes))
#         print('Check node', node.vertex_id, node.var_id)
#         RecursiveCleaningNodesFromDiagram(node,diagram)
#         print('lena', len(all_nodes))
#
# def RecursiveCleaningNodesFromDiagram(node,diagram):
#     if node.node_type is not DiagramNodeType.RootNode\
#             and len(node.high_parents) == 0\
#             and len(node.low_parents) == 0:
#         for child in node.high_childs:
#             child.high_parents = [x for x in child.high_parents if x is not node]
#             RecursiveCleaningNodesFromDiagram(child,diagram)
#         for child in node.low_childs:
#             child.low_parents = [x for x in child.low_parents if x is not node]
#             RecursiveCleaningNodesFromDiagram(child,diagram)
#         if node.hash_key in diagram.table_:
#             #print('del from table', (node.vertex_id, node.Value()))
#             del diagram.table_[node.hash_key]
#             if node.hash_key in diagram.table_:
#                 print('ERROR NO DEL')
#         print('del node', (node.vertex_id, node.Value()))
#         diagram.deleted_nodes_ += 1
#         del node

# def ConnectNodesDouble(host, lower, upper, diagram):
#     # проверяем количество родителей у узла, в которому приклеиваем
#     # если больше 1, то нужно будет его расклеивать
#     # когда склеиваем корни такой ситуации вообще не должно происходить
#     ungluing_flag = False
#     if upper.node_type != DiagramNodeType.QuestionNode:
#         if upper.node_type != DiagramNodeType.TrueNode:
#             if (len(upper.high_parents) + len(upper.low_parents)) > 1:
#                 print('Upper have more than 1 parent. Need ungluing.')
#                 ungluing_flag = True
#     if ungluing_flag == True:
#         diagram.new_nodes_ += 1
#         # тут нам надо расклеить узел на два так, чтобы у одного были все родители, кроме host
#         # а у второго только host
#         if host is None:
#             print('ERROR host is None, but try to ungluing')
#         old_upper = upper
#         print('Old upper', [old_upper.vertex_id, old_upper.Value(), old_upper])
#         upper = UngluingNode(upper, host)
#         print('New upper', [upper.vertex_id, upper.Value(), upper])
#
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