from Pathfinder import *
import pysat
from pysat.solvers import MapleChrono
from pysat.formula import CNF
from Draw import *
import gc

from Types import DiagramNode
import queue


def DJDtoBDD_separated(diagrams, numproc, order):
    current_djd_diagrams = diagrams
    counter = 0
    sys.setrecursionlimit(100000)
    iter_times = []
    conjoin_times = []
    subdjd_to_bdd_times = []
    current_bdd_diagrams = []
    # переводим каждую поддиаграмму в бдд
    p = multiprocessing.Pool(min(numproc, len(current_djd_diagrams)))
    jobs = [p.apply_async(DJDtoBDD, (djd_diagram,)) for djd_diagram in current_djd_diagrams]
    for job in jobs:
        new_bdd_diagram, transform_time = job.get()
        subdjd_to_bdd_times.append(transform_time)
        current_bdd_diagrams.append(new_bdd_diagram)
    p.close()
    p.join()
    current_bdd_diagrams = sorted(current_bdd_diagrams, key=lambda x: order.index(abs(x.main_root_.Value())))
    for index, diagram in enumerate(current_bdd_diagrams):
        # diagram.PrintProblem()
        diagram.PrintCurrentTable('SubBDDiagram ' + str(index + 1) + ':')
    # попарно объединяем поддиаграммы пока не останется одна финальная диаграмма
    while len(current_bdd_diagrams) > 1:
        current_bdd_diagrams = sorted(current_bdd_diagrams, key=lambda x: order.index(abs(x.main_root_.Value())))
        iter_start_time = time.time()
        counter += 1
        next_iter_diagrams = []
        current_nof_diagrams = len(current_bdd_diagrams)
        if len(current_bdd_diagrams) % 2 == 0:
            diagrams_pairs = list(make_pairs(current_bdd_diagrams))
        else:
            next_iter_diagrams.append(current_bdd_diagrams[-1])
            current_bdd_diagrams = current_bdd_diagrams[:-1]
            diagrams_pairs = list(make_pairs(current_bdd_diagrams))
        p = multiprocessing.Pool(min(numproc, len(diagrams_pairs)))
        print('\n\nCurrent iteration:', counter)
        print('Number of processes:', (min(len(diagrams_pairs), numproc)))
        print('Number of subdiagrams:', current_nof_diagrams)
        print('Number of tasks (pairs):', len(diagrams_pairs))
        # print('Pairs:', diagrams_pairs)
        jobs = [p.apply_async(ConjoinDJDs, (pair[0], pair[1])) for pair in diagrams_pairs]
        conjoin_times_iter = []
        for job in jobs:
            new_diagram, conjoin_time = job.get()
            print('\n Total number of actions with links to construct new diagram:', new_diagram.actions_with_links_)
            print(' Number of vertices in a result diagram:', new_diagram.VertexCount())
            print(' Number of links in a result diagram:', new_diagram.LinksCount())
            next_iter_diagrams.append(new_diagram)
            conjoin_times_iter.append(conjoin_time)
        p.close()
        p.join()
        current_bdd_diagrams = next_iter_diagrams
        # diagram1 = current_bdd_diagrams.pop(0)
        # diagram2 = current_bdd_diagrams.pop(0)
        # new_diagram = ConjoinDJDs(diagram1, diagram2)
        # current_bdd_diagrams.append(new_diagram)
        iter_time = time.time() - iter_start_time
        iter_times.append(iter_time)
        conjoin_times.append(conjoin_times_iter)
    final_diagram = current_bdd_diagrams[0]
    final_diagram.PrintCurrentTable('Final table:')
    print('Times for initial transformations', [round(x, 3) for x in subdjd_to_bdd_times])
    print('Sum of times for initial transformations', round(sum(subdjd_to_bdd_times), 3))
    print('Times for iterations', [round(x, 3) for x in iter_times])
    print('Sum of times for iterations:', round(sum(iter_times), 3))
    print('Times for conjoins by iteration:', [[round(y, 3) for y in x] for x in conjoin_times])
    print('Sum of times for conjoins by iteration:', round(sum([sum(x) for x in conjoin_times]), 3))
    return final_diagram


def make_pairs(diagrams):
    for i in range(0, len(diagrams), 2):
        yield tuple(diagrams[i:i + 2])


def ConjoinDJDs(diagram1, diagram2):
    conjoin_start_time = time.time()
    # соединяем две диаграммы в одну, чтобы потом избавляться от небинарностей
    sorted_nodes2 = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram2.order_, diagram2.table_.values())
    max_vertex = len(diagram1.table_)
    current_vertex_id = max_vertex+1
    print('\n\nDiagram 1:', diagram1)
    diagram1.PrintCurrentTable('Table 1:')
    print('\nDiagram 2:', diagram2)
    diagram2.PrintCurrentTable('Table 2:')
    for node in sorted_nodes2:
        node.vertex_id = current_vertex_id
        current_vertex_id += 1
    if type(diagram1) != DisjunctiveDiagram and type(diagram2) != DisjunctiveDiagram:
        diagram1.new_nodes_ += diagram2.new_nodes_
        diagram1.deleted_nodes_ += diagram2.deleted_nodes_
        diagram1.actions_with_links_ += diagram2.actions_with_links_
    DisjunctiveDiagramsBuilder.GluingNodes(sorted_nodes2, diagram1)
    EnumerateBDDiagramNodes(diagram1)
    # print('\n\nDiagram before remove nonbinary:', diagram1)
    # diagram1.PrintCurrentTable(' Table 3:')
    del diagram2
    diagram1.roots_ = diagram1.GetRoots()
    new_diagram, transform_time_ = DJDtoBDD(diagram1)
    print('\nDiagram after remove nonbinary:', new_diagram)
    new_diagram.PrintCurrentTable('New table:')
    conjoin_time = time.time() - conjoin_start_time
    return new_diagram, conjoin_time


def DJDtoBDD(djddiagram):
    start_transform_time = time.time()
    bdd_diagram = BDDiagram(djddiagram)
    transform_time = time.time() - start_transform_time
    return bdd_diagram, transform_time


class BDDiagram:
    # new_nodes_ = 0
    # deleted_nodes_ = 0
    # nonbinary_queue = []
    # changed_hash_nodes = set()
    # actions_with_links_ = 0
    def __init__(self, diagram):
        # print(type(diagram))
        if type(diagram) == DisjunctiveDiagram:
            self.new_nodes_ = 0
            self.deleted_nodes_ = 0
            self.nonbinary_queue = []
            self.changed_hash_nodes = set()
            self.actions_with_links_ = 0
        else:
            self.new_nodes_ = diagram.new_nodes_
            self.deleted_nodes_ = diagram.deleted_nodes_
            self.nonbinary_queue = []
            self.changed_hash_nodes = set()
            self.actions_with_links_ = diagram.actions_with_links_
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
        del diagram
        # print('BDD created with', self.actions_with_links_, 'number of actions with links')
        # self.PrintCurrentTable('Diagram before remove nonbinary')
        BDD_convert(self)
        # self.PrintCurrentTable('Diagram after remove nonbinary')
        # print('Number of actions with links', self.actions_with_links_, 'after conversion')
        CleaningDiagram(self)
        EnumerateBDDiagramNodes(self)
        # print('finish')

    # Возвращает таблицу
    def GetTable(self):
        return self.table_

    # Возвращает множество корней
    def GetRoots(self):
        self.roots_ = [x for x in self.table_.values() if x.node_type == DiagramNodeType.RootNode]
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
        return self.table_[hash_fnv('questionnode')]

    # Возвращает терминальный узел 1
    def GetTrueLeaf(self):
        return self.table_[hash_fnv('truenode')]

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

    def PrintCurrentTable(self, preambule=''):
        print('\n', preambule)
        if len(self.table_) > 0:
            sorted_nodes = DisjunctiveDiagramsBuilder.LitLessSortNodes(self.order_, self.table_.values())
            for node in sorted_nodes:
                node.PrintNode()
        else:
            print(' Empty table (all nodes are eliminated).')
            if self.problem_type_ == ProblemType.Cnf:
                print(' CNF is UNSAT.')
            elif self.problem_type_ == ProblemType.Dnf:
                print(' DNF is always SAT.')
            elif self.problem_type_ == ProblemType.Conflict:
                print(' Given conflict database is UNSAT.')
        print()

    def PrintCurrentTableJSON(self, filename):
        if len(self.table_) > 0:
            table_dict = dict()
            sorted_nodes = DisjunctiveDiagramsBuilder.LitLessSortNodes(self.order_, self.table_.values())
            for node in sorted_nodes:
                node_dict = dict()
                node_dict['variable'] = node.Value()
                node_dict['high_childs'] = ' '.join([(str(x.vertex_id) + '_' + str(x.Value())) for x in
                                                               node.high_childs])
                node_dict['low_childs'] = ' '.join([(str(x.vertex_id) + '_' + str(x.Value())) for x in
                                                              node.low_childs])
                node_dict['high_parents'] = ' '.join([(str(x.vertex_id) + '_' + str(x.Value())) for x in
                                                                node.high_parents])
                node_dict['low_parents'] = ' '.join([(str(x.vertex_id) + '_' + str(x.Value())) for x in
                                                               node.low_parents])
                table_dict[node.vertex_id] = node_dict
            #json_string = json.dumps(table_dict)
            with open(filename, 'w') as outfile:
                json.dump(table_dict, outfile, indent=2)
        else:
            print('Cannot dump diagram to json-file, because table is empty.')

    # Получаем КНФ из диаграммы (все пути из корней в терминальную 'true')
    def GetCNFFromBDD(self):
        cnf = []
        node_paths = []
        true_leaf = self.GetTrueLeaf()
        for node in true_leaf.high_parents:
            clause = []
            clause.append(node.var_id)
            node_path = []
            node_path.append(node)
            self.WritePaths(cnf, node_paths, node_path, clause)
        for node in true_leaf.low_parents:
            clause = []
            clause.append(-node.var_id)
            node_path = []
            node_path.append(node)
            self.WritePaths(cnf, node_paths, node_path, clause)
        NegateProblem(cnf)
        return cnf, node_paths


    # Получаем КНФ из диаграммы (все пути из корней в терминальную 'true')
    def GetPathsToTrue(self):
        cnf = []
        node_paths = []
        true_leaf = self.GetTrueLeaf()
        for node in true_leaf.high_parents:
            clause = []
            clause.append(node.var_id)
            node_path = []
            node_path.append(node)
            self.WritePaths(cnf, node_paths, node_path, clause)
        for node in true_leaf.low_parents:
            clause = []
            clause.append(-node.var_id)
            node_path = []
            node_path.append(node)
            self.WritePaths(cnf, node_paths, node_path, clause)
        return cnf, node_paths

    # Получаем выполняющие наборы из диаграммы (все пути из корней в терминальную 'question')
    def GetSatAssignmentFromDiagram(self):
        cnf = []
        node_paths = []
        question_leaf = self.GetQuestionLeaf()
        for node in question_leaf.high_parents:
            clause = []
            clause.append(node.var_id)
            node_path = []
            node_path.append(node)
            self.WritePaths(cnf, node_paths, node_path, clause)
        for node in question_leaf.low_parents:
            clause = []
            clause.append(-node.var_id)
            node_path = []
            node_path.append(node)
            self.WritePaths(cnf, node_paths, node_path, clause)
        return cnf, node_paths

    def WritePaths(self, problem, node_paths, node_path, clause):
        current_node: DiagramNode = node_path[-1]
        if current_node.IsRoot():
            clause.reverse()
            node_path.reverse()
            problem.append(clause)
            node_paths.append(node_path)
        else:
            for node in current_node.high_parents:
                hclause = copy.copy(clause)
                hnode_path = copy.copy(node_path)
                hclause.append(node.var_id)
                hnode_path.append(node)
                WritePaths(problem, node_paths, hnode_path, hclause)
            for node in current_node.low_parents:
                lclause = copy.copy(clause)
                lnode_path = copy.copy(node_path)
                lclause.append(-node.var_id)
                lnode_path.append(node)
                WritePaths(problem, node_paths, lnode_path, lclause)

    # Возвращает размер диаграммы в байтах
    def DiagramSize(self):
        size = 0
        for node in self.table_:
            size += node.Size()
        return size

    def __del__(self):
        for node in self.table_:
            del node

    def LinksCount(self):
        return sum([len(x.low_childs) + len(x.high_childs) for x in self.table_.values()])


def EnumerateBDDiagramNodes(diagram):
    vertex_id = 0
    for node in sorted(diagram.table_.values(), key=lambda x: diagram.order_.index(x.Value())):
        vertex_id += 1
        node.vertex_id = vertex_id


def BDD_convert(diagram):
    # print('\nInitial size of queue (should be 0)', len(diagram.nonbinary_queue))
    # if len(diagram.nonbinary_queue) > 0:
    #     for node in diagram.nonbinary_queue:
    #         node[0].PrintNode('  Node in queue:')
    # сперва надо свести корни к одному. для этого берём корень с наименьшим порядковым номером (относительно order)
    # затем добавляем ему ссылки на каждый другой корень причем и в high_childs и в low_childs
    # print('Initial number of nonbinary links in diagram is', diagram.NonBinaryLinkCount())
    # print('Initial number of nonbinary nodes in diagram is', diagram.NonBinaryNodesCount())
    sorted_roots_ = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_, diagram.roots_)
    # sorted_roots2_ = DisjunctiveDiagramsBuilder.LitLessSortNodeswrtOrderAndVertex(diagram.order_, diagram.roots_)
    # print('Sorted Roots', [(x.vertex_id, x.var_id) for x in sorted_roots_])
    # print('\nTable before roots gluing:')
    # diagram.PrintCurrentTable()
    main_root = sorted_roots_[-1]
    for i in range(len(sorted_roots_)-1):
        # print('Connect root', str(sorted_roots_[i].vertex_id) + '_' + str(sorted_roots_[i].var_id),
        #       ' to root', str(sorted_roots_[i+1].vertex_id) + '_' + str(sorted_roots_[i+1].var_id))
        # присоединяем нижний корень к верхнему по двум полярностям
        ConnectRoots(sorted_roots_[i+1], sorted_roots_[i],diagram)
    # теперь diagram.roots_ неправильная, потому что хэши поменялись (бтв, в table всё обновлено), но это и неважно
    # print('Roots', [(x.vertex_id, x.var_id, x.node_type) for x in diagram.roots_])
    diagram.main_root_ = main_root
    # print('Main root number:', main_root.vertex_id,'; variable:',main_root.var_id)
    # print('Current number of actions with links', diagram.actions_with_links_)
    # print('Number of nonbinary links in diagram after roots gluing is', diagram.NonBinaryLinkCount())
    # print('Number of nonbinary nodes in diagram after roots gluing is', diagram.NonBinaryNodesCount())
    # diagram.PrintCurrentTable('\nTable after roots gluing:')

    # Теперь вся диаграмма выходит из одного корня.
    # начинаем избавляться от небинарности. для этого сортируем узлы таблицы по (место в порядке, номер вершины)
    # и идём снизу вверх. если небинарность мы опустили вниз, то можно дальше убирать её в нижнем узле
    # а не заново строить и сортировать таблицу
    # print('\nAfter roots gluing size of queue (should be 0)', len(diagram.nonbinary_queue))
    # print('Start remove nonbinary links.')
    while diagram.NonBinaryNodesCount() > 0:
        # print('\n\nCurrent number of nonbinary nodes in diagram', diagram.NonBinaryNodesCount())
        # print('Current number of actions with links', diagram.actions_with_links_)
        sorted_nodes = DisjunctiveDiagramsBuilder.LitLessSortNodeswrtOrderAndVertex(diagram.order_, diagram.table_.values())
        # print('Current number of nodes', len(sorted_nodes))
        # print('Current number of deleted nodes', diagram.deleted_nodes_)
        first_nonbinary_node, polarity = FindFirstNonbinaryNode(sorted_nodes)
        # print('First nonbinary node', first_nonbinary_node.vertex_id, 'var', first_nonbinary_node.var_id)
        if polarity == 'both':
            diagram.nonbinary_queue.append([first_nonbinary_node, 1])
            diagram.nonbinary_queue.append([first_nonbinary_node, 0])
        # BDDiagram.nonbinary_queue.put([first_nonbinary_node, polarity])
        else:
            diagram.nonbinary_queue.append([first_nonbinary_node, polarity])
        # while not BDDiagram.nonbinary_queue.empty():
        while diagram.nonbinary_queue:
            # print('\nCurrent size of queue', len(diagram.nonbinary_queue))
            # diagram.PrintCurrentTable('\nCurrent table:')
            host = diagram.nonbinary_queue.pop()
            #host[0].PrintNode('Current host:')
            #print('Polarity:', host[1])
            # BDDiagram.PrintCurrentQueue(diagram)
            RemoveNonbinaryLink(host[0], host[1], diagram)
    #diagram.PrintCurrentTable('Table after BDD transformation:')
    #print('\nEnd size of queue (should be 0)', len(diagram.nonbinary_queue))


def RemoveNonbinaryLink(host, polarity, diagram):
    while (polarity == 1 and len(host.high_childs) > 1) or (polarity == 0 and len(host.low_childs) > 1):
        sorted_childs = DisjunctiveDiagramsBuilder.LitLessSortNodeswrtOrderAndVertex(diagram.order_,
                                                                                     (host.high_childs if polarity == 1
                                                                                      else host.low_childs))
        lower = sorted_childs[0]
        upper = sorted_childs[1]
        # host.PrintNode('\nCurrent host:')
        # lower.PrintNode('Current lower:')
        # upper.PrintNode('Current upper:')
        # diagram.PrintCurrentTable('RemoveNonbinaryLink 1 table:')
        host_upper_polarity = ConnectNodesDouble(host, polarity, lower, upper, diagram)
        if host_upper_polarity[2] == 'both':
            # если через очередь, то append заменяем на put
            diagram.nonbinary_queue.append([host_upper_polarity[1], 0])
            diagram.nonbinary_queue.append([host_upper_polarity[1], 1])
        elif host_upper_polarity[2] != 'no':
            diagram.nonbinary_queue.append([host_upper_polarity[1], host_upper_polarity[2]])
        host = host_upper_polarity[0]
        host_del = 'deleted'
        if host is host_del:
            break
        # diagram.PrintCurrentTable('RemoveNonbinaryLink 2 table:')


def FindFirstNonbinaryNode(sorted_nodes):
    for node in sorted_nodes:
        if len(node.high_childs) > 1 and len(node.low_childs) > 1:
            return node, 'both'
        elif len(node.high_childs) > 1:
            return node, 1
        elif len(node.low_childs) > 1:
            return node, 0


def ConnectRoots(upper, lower, diagram):
    # все корни просто соединяем последовательно двойными связями
    lower.node_type = DiagramNodeType.InternalNode
    host_upper_polarity = ConnectNodesDouble(None, None, lower, upper, diagram)


def ConnectNodesDouble(host, polarity, lower, upper, diagram):
    # diagram.PrintCurrentTable('ConnectNodesDouble 0 table:')
    # проверяем количество родителей у узла, в которому приклеиваем
    # если больше 1, то нужно будет его расклеивать
    # когда склеиваем корни такой ситуации вообще не должно происходить
    old_upper = upper
    upper = CheckNodeForUngluing(diagram, upper, host, polarity)
    # if old_upper is not upper:
    #     old_upper.PrintNode('Old upper:')
    #     upper.PrintNode('New upper:')

    # diagram.PrintCurrentTable('ConnectNodesDouble 1 table:')

    # удаляем из таблицы всё от upper (включительно) наверх
    diagram.changed_hash_nodes.clear()
    if host is not None:
        DeletingNodesFromTable(upper, diagram)
    else:
        del diagram.table_[upper.hash_key]


    # diagram.PrintCurrentTable('ConnectNodesDouble 2 table:')

    # print('\nАfter DeletingNodesFromTable New node')
    # upper.PrintNode()
    # print('New node highchilds')
    # for child in upper.high_childs:
    #     child.PrintNode()
    # print('New node lowchilds')
    # for child in upper.low_childs:
    #     child.PrintNode()
    # print()

    # затем, если хост есть, то удаляем связь host и lower
    if host is not None:
        RemoveLinkFromHostToLower(diagram, host, lower, polarity)


    # diagram.PrintCurrentTable('ConnectNodesDouble 3 table:')
    # print('\nАfter RemoveLinkFromHostToLower New node')
    # upper.PrintNode()
    # print('New node highchilds')
    # for child in upper.high_childs:
    #     child.PrintNode()
    # print('New node lowchilds')
    # for child in upper.low_childs:
    #     child.PrintNode()
    # print()

    # так как может сработать True-поглощение, то дети upper (если они поглотились 1-вершиной)
    # могут остаться без родителей, поэтому мы их тут запоминаем отдельно
    upper_old_high_childs = upper.high_childs.copy()
    upper_old_low_childs = upper.low_childs.copy()
    # upper.PrintNode('Upper before connect:')
    # lower.PrintNode('lower before connect:')
    # for parent in lower.low_parents:
    #     parent.PrintNode('  low parent:')
    # for parent in lower.high_parents:
    #     parent.PrintNode('  high parent:')
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
    # upper.PrintNode('Upper after connect:')
    # lower.PrintNode('lower after connect:')
    # for parent in lower.low_parents:
    #     parent.PrintNode('  low parent:')
    # for parent in lower.high_parents:
    #     parent.PrintNode('  high parent:')

    # diagram.PrintCurrentTable('ConnectNodesDouble 4 table:')
    # print('\nАfter connect lower to upper New node')
    # upper.PrintNode()
    # print('New node highchilds')
    # for child in upper.high_childs:
    #     child.PrintNode()
    # print('New node lowchilds')
    # for child in upper.low_childs:
    #     child.PrintNode()
    # print()

    # после чего, если у lower нет родителей больше (кроме host, ссылку на который мы удалили)
    # то удаляем lower (всех его детей мы передали, но лучше проверить)
    DeleteNodeWithoutParents(lower, diagram)

    # также нам надо проверить бывших детей upper на тоже самое
    for child in upper_old_high_childs:
        DeleteNodeWithoutParents(child, diagram)
    for child in upper_old_low_childs:
        DeleteNodeWithoutParents(child, diagram)

    # diagram.PrintCurrentTable('ConnectNodesDouble 5 table:')
    # print('\nАfter DeleteNodeWithoutParents New node')
    # upper.PrintNode()
    # print('New node highchilds')
    # for child in upper.high_childs:
    #     child.PrintNode()
    # print('New node lowchilds')
    # for child in upper.low_childs:
    #     child.PrintNode()
    # print()

    # Тут надо проверять, что если у upper 1-вершина по обеим полярностям в потомках
    # то мы его должны удалить, а его родителям добавить единицы по соответствующим полярностям
    # причем делать это рекурсивно
    # for x in diagram.changed_hash_nodes:
    #     x.PrintNode('\nChangedHash before:')
    upper, host = CheckForTrueNodes(upper, host, diagram)
    # for x in diagram.changed_hash_nodes:
    #     x.PrintNode('ChangedHash after:')


    upper_del = 'deleted'
    # возвращаем всё в таблицу с проверкой на склейку
    if host is not None:
        host, upper = GluingNodes(upper, host, diagram)
    elif upper is not upper_del:
        upper.HashKey()
        diagram.table_[upper.hash_key] = upper


    # diagram.PrintCurrentTable('ConnectNodesDouble 6 table:')
    if upper is not upper_del:
        # проверяем небинарность upper
        if len(upper.high_childs) > 1 and len(upper.low_childs) > 1:
            upper_nonbinary_polarity = 'both'
        elif len(upper.high_childs) > 1:
            upper_nonbinary_polarity = 1
        elif len(upper.low_childs) > 1:
            upper_nonbinary_polarity = 0
        else:
            upper_nonbinary_polarity = 'no'
    else:
        upper_nonbinary_polarity = 'no'

    return [host, upper, upper_nonbinary_polarity]


def RemoveLinkFromHostToLower(diagram, host, lower, polarity):
    # print('RemoveLinkFromHostToLower before Host:', end=' ')
    # host.PrintNode()
    # print('RemoveLinkFromHostToLower before Lower:', end=' ')
    # lower.PrintNode()
    if polarity == 1:
        host_len_childs_before = len(host.high_childs)
        lower_len_parents_before = len(lower.high_parents)
        if lower in host.high_childs:
            diagram.actions_with_links_ += 1
            host.high_childs = [x for x in host.high_childs if x is not lower]
            if host in lower.high_parents:
                diagram.actions_with_links_ += 1
                lower.high_parents = [x for x in lower.high_parents if x is not host]
            else:
                print('ERROR there is no high_parent link from lower to host')
                raise Exception('ERROR there is no high_parent link from lower to host')
        else:
            print('ERROR polarity is 1, but there is no high_child link from host to lower')
            raise Exception('ERROR polarity is 1, but there is no high_child link from host to lower')
        # if host_len_childs_before-len(host.high_childs) != 1:
        #     print('ERROR removed more than 1 link from host high childs')
        #     raise Exception('ERROR removed more than 1 link from host high childs')
        # if lower_len_parents_before-len(lower.high_parents) != 1:
        #     print('ERROR removed more than 1 link from lower high parents')
        #     raise Exception('ERROR removed more than 1 link from lower high parents')
    elif polarity == 0:
        if lower in host.low_childs:
            diagram.actions_with_links_ += 1
            host.low_childs = [x for x in host.low_childs if x is not lower]
            if host in lower.low_parents:
                diagram.actions_with_links_ += 1
                lower.low_parents = [x for x in lower.low_parents if x is not host]
            else:
                print('ERROR there is no low_parent link from lower to host')
                raise Exception('ERROR there is no low_parent link from lower to host')
        else:
            print('ERROR polarity is 0, but there is no low_child link from host to lower')
            raise Exception('ERROR polarity is 0, but there is no low_child link from host to lower')
    else:
        print('ERROR Host is not None, but polarity not 0 or 1.')
        raise Exception('ERROR Host is not None, but polarity not 0 or 1.')
    # print('RemoveLinkFromHostToLower after Host:', end=' ')
    # host.PrintNode()
    # print('RemoveLinkFromHostToLower after Lower:', end=' ')
    # lower.PrintNode()


def CheckNodeForUngluing(diagram, upper, host, polarity):
    if upper.node_type != DiagramNodeType.QuestionNode:
        if upper.node_type != DiagramNodeType.TrueNode:
            if (len(upper.high_parents) + len(upper.low_parents)) > 1:
                #print('Upper have more than 1 parent. Need ungluing.')
                diagram.new_nodes_ += 1
                # тут нам надо расклеить узел на два так, чтобы у одного были все родители, кроме host
                # а у второго только host
                if host is None:
                    print('ERROR host is None, but try to ungluing')
                    raise Exception('ERROR host is None, but try to ungluing')
                #print('Old upper')
                #upper.PrintNode()
                new_upper = UngluingNode(upper, host, polarity, diagram)
                # new_upper.PrintNode('New upper:')
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
            diagram.actions_with_links_ += 1
            upper.high_childs.append(lower)
            upper.high_childs = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_, upper.high_childs)
        if upper not in lower.high_parents:
            diagram.actions_with_links_ += 1
            lower.high_parents.append(upper)
            lower.high_parents = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_, lower.high_parents)
        if question_leaf in upper.high_childs and len(upper.high_childs) > 1:
            diagram.actions_with_links_ += 1
            upper.high_childs.remove(question_leaf)
            question_leaf.high_parents = [x for x in question_leaf.high_parents if x is not upper]
    if true_leaf not in upper.low_childs:
        if lower not in upper.low_childs:
            diagram.actions_with_links_ += 1
            upper.low_childs.append(lower)
            upper.low_childs = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_, upper.low_childs)
        if upper not in lower.low_parents:
            diagram.actions_with_links_ += 1
            lower.low_parents.append(upper)
            lower.low_parents = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_, lower.low_parents)
        if question_leaf in upper.low_childs and len(upper.low_childs) > 1:
            diagram.actions_with_links_ += 1
            upper.low_childs.remove(question_leaf)
            question_leaf.low_parents = [x for x in question_leaf.low_parents if x is not upper]


def TranferChildsFromLowerToUpper(diagram, upper, lower):
    if diagram.GetTrueLeaf() not in upper.high_childs:
        if diagram.GetTrueLeaf() in lower.high_childs:
            SetTrueChild(diagram, upper, 1)
        else:
            for high_child in lower.high_childs:
                if high_child not in upper.high_childs:
                    diagram.actions_with_links_ += 1
                    upper.high_childs.append(high_child)
                    high_child.high_parents.append(upper)
                    high_child.high_parents = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_,
                                                                                          high_child.high_parents)
            if len(upper.high_childs) > 1 and diagram.GetQuestionLeaf() in upper.high_childs:
                RemoveLink(upper, diagram.GetQuestionLeaf(), 1)
            upper.high_childs = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_, upper.high_childs)
    if diagram.GetTrueLeaf() not in upper.low_childs:
        if diagram.GetTrueLeaf() in lower.low_childs:
            SetTrueChild(diagram, upper, 0)
        else:
            for low_child in lower.low_childs:
                if low_child not in upper.low_childs:
                    diagram.actions_with_links_ += 1
                    upper.low_childs.append(low_child)
                    low_child.low_parents.append(upper)
                    low_child.low_parents = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_,
                                                                                        low_child.low_parents)
            if len(upper.low_childs) > 1 and diagram.GetQuestionLeaf() in upper.low_childs:
                RemoveLink(upper, diagram.GetQuestionLeaf(), 0)
            upper.low_childs = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_, upper.low_childs)


def RemoveLink(parent, child, polarity):
    if polarity == 0:
        parent.low_childs = set([x for x in parent.low_childs if x is not child])
        child.low_parents = [x for x in child.low_parents if x is not parent]
    elif polarity == 1:
        parent.high_childs = set([x for x in parent.high_childs if x is not child])
        child.high_parents = [x for x in child.high_parents if x is not parent]

def CheckNonbinaryWithTrueNode(node, diagram):
    #print('\nCheckNonbinaryWithTrueNode')
    #node.PrintNodeWithoutParents()
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
    #print('\nCheckNonbinaryWithQuestionNode')
    #node.PrintNodeWithoutParents()
    question_leaf = diagram.GetQuestionLeaf()
    if len(node.high_childs) > 1 and question_leaf in node.high_childs:
        node.high_childs.remove(question_leaf)
        if node in question_leaf.high_parents:
            question_leaf.high_parents = [x for x in question_leaf.high_parents if x is not node]
        else:
            print('ERROR exist high_child link "node->?", but not exist reversed parent link')
            raise Exception('ERROR exist high_child link "node->?", but not exist reversed parent link')
    if len(node.low_childs) > 1 and question_leaf in node.low_childs:
        node.low_childs.remove(question_leaf)
        if node in question_leaf.low_parents:
            question_leaf.low_parents = [x for x in question_leaf.low_parents if x is not node]
        else:
            print('ERROR exist low_child link "node->?", but not exist reversed parent link')
            raise Exception('ERROR exist low_child link "node->?", but not exist reversed parent link')


def SetTrueChild(diagram, node, polarity):
    if polarity == 1:
        for child in node.high_childs:
            diagram.actions_with_links_ += 1
            child.high_parents = [x for x in child.high_parents if x is not node]
        diagram.actions_with_links_ += 1
        node.high_childs = [diagram.GetTrueLeaf()]
        diagram.GetTrueLeaf().high_parents.append(node)
    elif polarity == 0:
        for child in node.low_childs:
            diagram.actions_with_links_ += 1
            child.low_parents = [x for x in child.low_parents if x is not node]
        diagram.actions_with_links_ += 1
        node.low_childs = [diagram.GetTrueLeaf()]
        diagram.GetTrueLeaf().low_parents.append(node)


def UngluingNode(original_node, host, polarity, diagram):
    # сперва создаем узел с тем же типом, той же переменной и теми же детьми
    diagram.actions_with_links_ += len(original_node.high_childs) + len(original_node.low_childs)
    new_node = DiagramNode(original_node.node_type, original_node.var_id, original_node.high_childs,
                           original_node.low_childs)
    # и добавляем его в родители детей
    AddNodeToParentsOfChilds(new_node, diagram)
    if polarity is None:
        print('ERROR Polarity None when ungluing node')
        raise Exception('ERROR Polarity None when ungluing node')
    # затем убираем upper из родителей original_node
    # и удаляем ссылку из upper на original_node
    if polarity == 1:
        if host in original_node.high_parents:
            diagram.actions_with_links_ += 1
            original_node.high_parents = [x for x in original_node.high_parents if x is not host]
            if original_node in host.high_childs:
                diagram.actions_with_links_ += 1
                host.high_childs = [x for x in host.high_childs if x is not original_node]
            else:
                print('ERROR ungluing node 1 high (no old upper in host highchilds)')
                raise Exception('ERROR ungluing node 1 high (no old upper in host highchilds)')
        else:
            print('Old upper high parents:', [(x.vertex_id, x.var_id) for x in original_node.high_parents])
            print('Host', end=' ')
            host.PrintNodeWithoutParents()
            print('ERROR ungluing node 2 high (no host in old upper highparents)')
            raise Exception('ERROR ungluing node 2 high (no host in old upper highparents)')
    elif polarity == 0:
        if host in original_node.low_parents:
            diagram.actions_with_links_ += 1
            original_node.low_parents = [x for x in original_node.low_parents if x is not host]
            if original_node in host.low_childs:
                diagram.actions_with_links_ += 1
                host.low_childs = [x for x in host.low_childs if x is not original_node]
            else:
                print('ERROR ungluing node 1 low')
                raise Exception('ERROR ungluing node 1 low')
        else:
            print('ERROR ungluing node 2 low')
            raise Exception('ERROR ungluing node 2 low')

    # работаем с new_node. добавляем ему host в родители по нужной полярности
    # а host'у добавляем new_node в дети по той же полярности
    if polarity == 1:
        diagram.actions_with_links_ += 1
        new_node.high_parents.append(host)
        host.high_childs.append(new_node)
    elif polarity == 0:
        diagram.actions_with_links_ += 1
        new_node.low_parents.append(host)
        host.low_childs.append(new_node)
    else:
        print('ERROR ungluing node no polarity')
        raise Exception('ERROR ungluing node no polarity')
    # проверка чтобы new_node был где надо
    # print('\nRight after ungluing New node')
    # new_node.PrintNode()
    # print('New node highchilds')
    # for child in new_node.high_childs:
    #     child.PrintNode()
    # print('New node lowchilds')
    # for child in new_node.low_childs:
    #     child.PrintNode()
    # print()
    return new_node


def DeleteNodeWithoutParents(node, diagram):
    if len(node.high_parents) + len(node.low_parents) == 0:
        if node.hash_key in diagram.table_ and diagram.table_[node.hash_key] is node:
            del diagram.table_[node.hash_key]
        # при удалении узла мы удаляем ссылки на него из детей
        # node.PrintNode('Delete node without parents:')
        for low_child in node.low_childs:
            # low_child.PrintNode('  Low child before:')
            diagram.actions_with_links_ += 1
            low_child.low_parents = [x for x in low_child.low_parents if x is not node]
            DeleteNodeWithoutParents(low_child, diagram)
            # low_child.PrintNode('  Low child after:')
        #print('High childs:')
        for high_child in node.high_childs:
            #print('High child before:', end=' ')
            #high_child.PrintNode()
            diagram.actions_with_links_ += 1
            high_child.high_parents = [x for x in high_child.high_parents if x is not node]
            DeleteNodeWithoutParents(high_child, diagram)
            #print('High child after:', end=' ')
            #high_child.PrintNode()
        # for x in diagram.changed_hash_nodes:
        #     x.PrintNode('ChangedHash before 2:')
        if node in diagram.changed_hash_nodes:
            # а если это lower без родителей, то его там нету
            # node.PrintNode('DeleteNodeWithoutParents del node from diagram.changed_hash_nodes')
            # diagram.changed_hash_nodes.remove(node)
            diagram.changed_hash_nodes = set([x for x in diagram.changed_hash_nodes if x is not node])
            # дальше идёт проверка остался ли узел в changed_hash_nodes, но она не имеет смысла,
            # так как самого узла то там нет, а вот его копия вполне может быть
            # if node in diagram.changed_hash_nodes:
            #     print('ERROR node still in diagram.changed_hash_nodes')
            #     node.PrintNode(' Deleting node')
            #     for node_ in diagram.changed_hash_nodes:
            #         node_.PrintNode('  Changed hash node:')
            #     raise Exception('ERROR node still in diagram.changed_hash_nodes')
        # for x in diagram.changed_hash_nodes:
        #     x.PrintNode('ChangedHash after 2:')
        if node in [x[0] for x in diagram.nonbinary_queue]:
            # опять же сюда lower попадать не должен
            # node.PrintNode('DeleteNodeWithoutParents del node from nonbinary_queue')
            diagram.nonbinary_queue = [x for x in diagram.nonbinary_queue if x[0] is not node]
            for node_ in [x[0] for x in diagram.nonbinary_queue]:
                if node_ is node:
                    node.PrintNode(' Deleting node')
                    for node__ in [x[0] for x in diagram.nonbinary_queue]:
                        node__.PrintNode('  nonbinary_queue node:')
                    raise Exception('ERROR node still in diagram.nonbinary_queue')
        diagram.deleted_nodes_ += 1
        del node


def CheckForTrueNodes(node, host, diagram):
    if diagram.GetTrueLeaf() in node.low_childs and \
            diagram.GetTrueLeaf() in node.high_childs:
        # node.PrintNode('\nDouble True child deleting node:')
        # for parent in node.high_parents:
        #     parent.PrintNode('    High parent:')
        # for parent in node.low_parents:
        #     parent.PrintNode('    Low parent:')
        for hp in node.high_parents:
            SetTrueChild(diagram, hp, 1)
            node_, host = CheckForTrueNodes(hp, host, diagram)
        for lp in node.low_parents:
            SetTrueChild(diagram, lp, 0)
            node_, host = CheckForTrueNodes(lp, host, diagram)
        if len(node.high_parents) + len(node.low_parents) == 0:
            # node.PrintNode('Double True child deleted node:')
            # print(sys.getrefcount(node))
            # print(gc.get_referrers(node))
            if node is host:
                host = 'deleted'
                # print('Host is deleted during True-Nodes Elimination.')
            # for x in diagram.changed_hash_nodes:
            #     x.PrintNode('ChangedHash before 1:')
            DeleteNodeWithoutParents(node, diagram)
            # for x in diagram.changed_hash_nodes:
            #     x.PrintNode('ChangedHash after 1:')
            # print(sys.getrefcount(node))
            # print(gc.get_referrers(node))
            # node.PrintNode('deleted node after deleting:')
            return 'deleted', host
        else:
            node.PrintNode('True node still has parents')
            raise Exception('ERROR True node still has parents')
    else:
        return node, host


def AddNodeToParentsOfChilds(new_node, diagram):
    # эта функция нужна при создании новых узлов вне процедуры построения DJD,
    # так как в __init__ нет работы с родителями
    diagram.actions_with_links_ += len(new_node.high_childs) + len(new_node.low_childs)
    for child in new_node.high_childs:
        child.high_parents.append(new_node)
    for child in new_node.low_childs:
        child.low_parents.append(new_node)


def GluingNodes(upper, host, diagram):
    nodes_with_changed_hash = DisjunctiveDiagramsBuilder.LitLessSortNodeswrtOrderAndVertex(diagram.order_,
                                                                                           diagram.changed_hash_nodes)
    new_upper = upper
    new_host = host
    for node in nodes_with_changed_hash:
        node.HashKey()
        if node.hash_key in diagram.table_ and diagram.table_[node.hash_key] is not node:
            node_to_which_glue = diagram.table_[node.hash_key]
            if node is node_to_which_glue:
                print('ERROR')
            # node.PrintNode('Glued node')
            # node_to_which_glue.PrintNode('with node')
            if node is upper:
                new_upper = node_to_which_glue
            elif node is host:
                # print('Host changed')
                new_host = node_to_which_glue
            for node_pol in diagram.nonbinary_queue:
                if node_pol[0] is node:
                    node_pol[0] = node_to_which_glue
            GluingNode(node, node_to_which_glue, diagram)
            del node
            diagram.deleted_nodes_ += 1
        else:
            # node.PrintNode('Return node to table:')
            diagram.table_[node.hash_key] = node
    return new_host, new_upper

def GluingNode(node, node_to_which_glue, diagram):
    # заменяем ссылки в родителях
    ReplaceParentsLinksToNode(node, node_to_which_glue, diagram)
    # Удаляем ссылки потомков узла на него
    DeleteChildsLinksToNode(node, diagram)


def ReplaceParentsLinksToNode(node,node_to_which_glue, diagram):
    for parent in node.high_parents:
        diagram.actions_with_links_ += 1
        parent.high_childs = [x for x in parent.high_childs if x is not node and x is not node_to_which_glue]
        parent.high_childs.append(node_to_which_glue)
        for tmpnode in node_to_which_glue.high_parents:
            if tmpnode is parent:
                break
        else:
            #print('add as highparent ', (parent.Value(), parent), 'to node', (it_node.Value(), it_node))
            node_to_which_glue.high_parents.append(parent)
    for parent in node.low_parents:
        diagram.actions_with_links_ += 1
        parent.low_childs = [x for x in parent.low_childs if x is not node and x is not node_to_which_glue]
        parent.low_childs.append(node_to_which_glue)
        for tmpnode in node_to_which_glue.low_parents:
            if tmpnode is parent:
                break
        else:
            node_to_which_glue.low_parents.append(parent)
            #print('add as lowparent ', (parent.Value(), parent), 'to node', (it_node.Value(), it_node))


def DeleteChildsLinksToNode(node, diagram):
    diagram.actions_with_links_ += len(node.high_childs) + len(node.low_childs)
    for child in node.high_childs:
        child.high_parents = [x for x in child.high_parents if x is not node]
    for child in node.low_childs:
        child.low_parents = [x for x in child.low_parents if x is not node]


# Рекурсивное удаление узлов из таблицы от node наверх
def DeletingNodesFromTable(node, diagram):
    diagram.changed_hash_nodes.add(node)
    if node.hash_key in diagram.table_ and \
        node is not diagram.GetTrueLeaf() and \
        node is not diagram.GetQuestionLeaf():
        if diagram.table_[node.hash_key] is node:
            # node.PrintNode('Delete from table:')
            del diagram.table_[node.hash_key]
        for parent in set(node.high_parents + node.low_parents):
            DeletingNodesFromTable(parent, diagram)


def CleaningDiagram(diagram):
    sorted_nodes = DisjunctiveDiagramsBuilder.LitLessSortNodeswrtOrderAndVertex(diagram.order_, diagram.table_.values())
    for node in sorted_nodes:
        if len(node.low_childs) > 0 and len(node.high_childs) > 0:
            if node.low_childs[0] is node.high_childs[0]:
                diagram.changed_hash_nodes.clear()
                # print('Diagram:', diagram)
                # diagram.PrintCurrentTable('Table before deletion of useless node')
                DeletingNodesFromTable(node, diagram)
                # node.PrintNode('Delete useless node:')
                DeleteUselessNode(node, diagram)
                host_, upper_ = GluingNodes(None, None, diagram)


def DeleteUselessNode(node, diagram):
    # удаляем вершину из списка вершин с изменившимся хэшем
    if node in diagram.changed_hash_nodes:
        diagram.changed_hash_nodes = set([x for x in diagram.changed_hash_nodes if x is not node])
        # if node in diagram.changed_hash_nodes:
        #     print('ERROR node still in diagram.changed_hash_nodes')
        #     node.PrintNode(' Deleting node')
        #     for node_ in diagram.changed_hash_nodes:
        #         node_.PrintNode('  Changed hash node:')
        #     raise Exception('ERROR node still in diagram.changed_hash_nodes')

    # переносим связь вершины с 1-потомком 1-родителю (у родителя точно 1 потомок по 1-связи, а вот у
    # потомка может быть больше 1 родителя, если это терминальная вершина)
    node.high_childs[0].high_parents = [x for x in node.high_childs[0].high_parents if x is not node]
    if len(node.high_parents) > 0:
        # node.high_parents[0].PrintNode('   high parent before')
        # node.high_childs[0].PrintNode('   high child before')
        node.high_parents[0].high_childs[0] = node.high_childs[0]
        node.high_childs[0].high_parents.append(node.high_parents[0])
        # node.high_parents[0].PrintNode('   high parent after')
        # node.high_childs[0].PrintNode('   high child after')

    # переносим связь вершины с 0-потомком 0-родителю
    node.low_childs[0].low_parents = [x for x in node.low_childs[0].low_parents if x is not node]
    if len(node.low_parents) > 0:
        # node.low_parents[0].PrintNode('   low parent before')
        # node.low_childs[0].PrintNode('   low child before')
        node.low_parents[0].low_childs[0] = node.low_childs[0]
        node.low_childs[0].low_parents.append(node.low_parents[0])
        # node.low_parents[0].PrintNode('   low parent after')
        # node.low_childs[0].PrintNode('   low child after')

    del node

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