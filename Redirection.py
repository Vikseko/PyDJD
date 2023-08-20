from Pathfinder import *
import pysat
from pysat.solvers import MapleChrono
from pysat.formula import CNF

from Types import DiagramNode, DiagramNodeType


def PathsRedirection(diagram, problem):
    nof_redir_copy_paths = 0
    nof_redir_uniq_paths = 0
    cnf = copy.deepcopy(problem)
    list_hard_assumptions = []
    cnf, tmp_ = GetCNFFromDiagram(diagram)
    cnf = CNF(from_clauses=cnf)
    g = MapleChrono(bootstrap_with=cnf)
    lit_paths, node_paths = GetQuestionPathsFromDiagram(diagram)
    print('Number of question paths:'.ljust(30, ' '), len(node_paths))
    redir_pairs = []
    for lit_path, node_path in zip(lit_paths, node_paths):
        s, model = PathCheck_v1(lit_path,g, list_hard_assumptions)
        if s == False:
            redir_pairs.append([lit_path,node_path])
        if s == None:
            continue
        if s == True:
            #print('Problem solved due false path checking.')
            #print('Model:', model)
            #break
            pass
    print('Number of solved assumptions'.ljust(30, ' '), len(node_paths) - len(list_hard_assumptions))
    print('Number of hard assumptions'.ljust(30,' '), len(list_hard_assumptions))
    cnf1 = CNF(from_clauses=[x[0] for x in redir_pairs]).clauses
    cnf1 = copy.deepcopy(cnf1)
    NegateProblem(cnf1)
    cnf1 = CNF(from_clauses=cnf1)
    cnf1.to_file('redir_lits.cnf')
    for pair in redir_pairs:
        lit_path = pair[0]
        node_path = pair[1]
        flag_copy_path = RedirectPath_v1(lit_path, node_path, diagram, node_paths)
        if flag_copy_path == True:
            nof_redir_copy_paths += 1
        else:
            nof_redir_uniq_paths += 1
    FixRootType(diagram)
    print('Number of copy redirected'.ljust(30, ' '), nof_redir_copy_paths)
    print('Number of uniq redirected'.ljust(30, ' '), nof_redir_uniq_paths)


def PathCheck(lit_path, solver):
    timer = Timer(0.01, interrupt, [solver])
    timer.start()
    s = solver.solve_limited(assumptions=lit_path, expect_interrupt=True)
    solver.clear_interrupt()
    timer.cancel()
    if s == None:
        return s, None
    elif s == False:
        return s, None
    elif s == True:
        model = solver.get_model()
        return s, model


def interrupt(s):
    s.interrupt()


def RedirectPath(lit_path,node_path,diagram):
    # Проверяем, чтобы первый узел был корнем
    if node_path[0].node_type != DiagramNodeType.RootNode:
        raise RuntimeError('First node in node_path isnt RootNode')
    # Находим первый узел, у которого больше 1 родителя
    copy_index = None
    for i in range(len(node_path)):
        node = node_path[i]
        nof_parents = len(node.high_parents) + len(node.low_parents)
        if nof_parents > 1:
            copy_index = i
            break
    # Перенаправляем путь
    if copy_index != None:
        # Путь нужно скопировать для перенаправления
        RedirCopyPath(copy_index, lit_path, node_path, diagram)
        return True
    else:
        # Копирование не требуется
        RedirOriginalPath(lit_path[-1],node_path[-1],diagram)
        return False


def RedirCopyPath(copy_index, lit_path, node_path, diagram):
    old_nodes = node_path[copy_index:]
    old_lits = lit_path[copy_index:]
    redir_node = node_path[copy_index-1]
    redir_lit = lit_path[copy_index-1]
    copylink_pair = (node_path[copy_index-1], node_path[copy_index])
    #print('copylink pair', [(x.Value(),x) for x in copylink_pair])
    # Рекурсивно удаляем из таблицы узлы от последнего в пути наверх
    deleted_nodes = set()
    DeletingNodesFromTable(redir_node, diagram, deleted_nodes)
    # Копируем узлы и перенаправляем путь
    new_nodes = CopyNodes(redir_node, redir_lit, old_nodes, old_lits, diagram)
    # Работаем с copylink_pair в node_paths
    # Добавляем узлы в таблицу, проверяя склейку
    deleted_nodes.update(new_nodes)
    GluingNodes(deleted_nodes, diagram)



def CopyNodes(redir_node, redir_lit, old_nodes, old_lits, diagram):
    # Копируем узлы
    new_nodes = []
    for node in old_nodes:
        copy_node = DiagramNode(node.node_type, node.var_id, node.high_childs, node.low_childs)
        new_nodes.append(copy_node)
    # перенаправляем ссылки на детей внутри скопированного пути
    for i in reversed(range(len(new_nodes))):
        RedirLinksFromOldToCopy(new_nodes, old_nodes, old_lits, i, diagram)
    # Добавляем ссылки на родителей внутри пути
    AddParentLinkInCopyPath(new_nodes)
    # Работаем с redirection link (ссылка между copylink_pair)
    if redir_lit < 0:
        redir_node.low_childs = [node for node in redir_node.low_childs if node is not old_nodes[0]]
        old_nodes[0].low_parents = [node for node in old_nodes[0].low_parents if node is not redir_node]
        #if redir_node.Value() == 142:
            #print('redir',(redir_node.Value(), redir_node),'from low ',(old_nodes[0].Value(),old_nodes[0]),'to',(new_nodes[0].Value(),new_nodes[0]))
        redir_node.low_childs.append(new_nodes[0])
        new_nodes[0].low_parents.append(redir_node)
    else:
        redir_node.high_childs = [node for node in redir_node.high_childs if node is not old_nodes[0]]
        old_nodes[0].high_parents = [node for node in old_nodes[0].high_parents if node is not redir_node]
        #if redir_node.Value() == 142:
            #print('redir',(redir_node.Value(), redir_node),'from high ',(old_nodes[0].Value(),old_nodes[0]),'to',(new_nodes[0].Value(),new_nodes[0]))
        redir_node.high_childs.append(new_nodes[0])
        new_nodes[0].high_parents.append(redir_node)
    return new_nodes


def RedirLinksFromOldToCopy(new_nodes, old_nodes, old_lits, i, diagram):
    if i < len(new_nodes) - 1:
        if old_lits[i] < 0:
            # Меняем ссылку внутри пути в low_childs
            new_nodes[i].low_childs = [node for node in new_nodes[i].low_childs if node is not old_nodes[i+1]]
            new_nodes[i].low_childs.append(new_nodes[i+1])
        else:
            # Меняем ссылку внутри пути в high_childs
            new_nodes[i].high_childs = [node for node in new_nodes[i].high_childs if node is not old_nodes[i+1]]
            new_nodes[i].high_childs.append(new_nodes[i+1])
    else:
        if old_lits[i] < 0:
            # Меняем ссылку на терминальную вершину в low_childs
            new_nodes[i].low_childs = [node for node in new_nodes[i].low_childs if node is not diagram.GetQuestionLeaf()]
            new_nodes[i].low_childs.append(diagram.GetTrueLeaf())
            #diagram.GetTrueLeaf().low_parents.append(new_nodes[i])
        else:
            # Меняем ссылку на терминальную вершину в high_childs
            new_nodes[i].high_childs = [node for node in new_nodes[i].high_childs if node is not diagram.GetQuestionLeaf()]
            new_nodes[i].high_childs.append(diagram.GetTrueLeaf())
            #diagram.GetTrueLeaf().high_parents.append(new_nodes[i])
    new_nodes[i].HashKey()


def AddParentLinkInCopyPath(new_nodes):
    for node in new_nodes:
        for child in node.high_childs:
            child.high_parents.append(node)
        for child in node.low_childs:
            child.low_parents.append(node)


def ReplaceCopyNodesInNodePaths(node_paths, new_nodes, old_nodes, copylink_pair):
    for node_path in node_paths:
        replace_flag = False
        replace_index = None
        for i in range(len(node_path)-1):
            if (node_path[i] is copylink_pair[0]) and (node_path[i+1] is copylink_pair[1]):
                replace_flag = True
                replace_index = i+1
                break
        if replace_flag == True:
            for i in range(replace_index,len(node_path)):
                stop_flag = True
                for j in range(len(old_nodes)):
                    if (node_path[i] is old_nodes[j]) and (new_nodes[j] is not old_nodes[j]):
                        node_path[i] = new_nodes[j]
                        stop_flag = False
                        break
                if (stop_flag == True):
                    break


def RedirOriginalPath(last_lit, last_node, diagram):
    # Рекурсивно удаляем из таблицы узлы от последнего в пути наверх
    deleted_nodes = set()
    DeletingNodesFromTable(last_node,diagram, deleted_nodes)
    quest_leaf = diagram.GetQuestionLeaf()
    # Перенаправляем путь
    if last_lit < 0:
        for i in range(len(last_node.low_childs)):
            if last_node.low_childs[i] == diagram.GetQuestionLeaf():
                last_node.low_childs[i] = diagram.GetTrueLeaf()
                break
        quest_leaf.low_parents = [x for x in quest_leaf.low_parents if x is not last_node]
        diagram.GetTrueLeaf().low_parents.append(last_node)
    else:
        for i in range(len(last_node.high_childs)):
            if last_node.high_childs[i] == diagram.GetQuestionLeaf():
                last_node.high_childs[i] = diagram.GetTrueLeaf()
                break
        quest_leaf.high_parents = [x for x in quest_leaf.high_parents if x is not last_node]
        diagram.GetTrueLeaf().high_parents.append(last_node)
    # Проверяем ранее удаленные из таблицы узлы на склейку
    GluingNodes(deleted_nodes, diagram)


# Рекурсивное удаление узлов из таблицы от node наверх
def DeletingNodesFromTable(node, diagram, deleted_nodes):
    deleted_nodes.add(node)
    if node.hash_key in diagram.table_ and node is not diagram.GetTrueLeaf() and node is not diagram.GetQuestionLeaf():
        del diagram.table_[node.hash_key]
        for parent in set(node.high_parents+node.low_parents):
            DeletingNodesFromTable(parent, diagram, deleted_nodes)


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


def ReplaceNodeInNodePaths(node,it_node,node_paths):
    for path in node_paths:
        for i in range(len(path)):
            if path[i] is node:
                path[i] = it_node



def FixRootType(diagram):
    node = diagram.GetTrueLeaf()
    FixRootTypeRecursive(node)
    node = diagram.GetQuestionLeaf()
    FixRootTypeRecursive(node)

def FixRootTypeRecursive(node):
    if (len(node.high_parents) + len(node.low_parents) == 0) and (node.node_type != DiagramNodeType.RootNode):
        print('root type fixed')
        node.node_type = DiagramNodeType.RootNode
    else:
        for parent in node.high_parents:
            FixRootTypeRecursive(parent)
        for parent in node.low_parents:
            FixRootTypeRecursive(parent)


def PathCheck_v1(lit_path, solver, list_hard_assumptions):
    timer = Timer(0.01, interrupt, [solver])
    timer.start()
    s = solver.solve_limited(assumptions=lit_path, expect_interrupt=True)
    solver.clear_interrupt()
    if s == None:
        list_hard_assumptions.append(lit_path)
        return s, None
    elif s == False:
        return s, None
    elif s == True:
        model = solver.get_model()
        return s, model


def RedirectPath_v1(lit_path,node_path,diagram, node_paths):
    # Проверяем, чтобы первый узел был корнем
    if node_path[0].node_type != DiagramNodeType.RootNode:
        raise RuntimeError('First node in node_path isnt RootNode')
    # Находим первый узел, у которого больше 1 родителя
    copy_index = None
    for i in range(len(node_path)):
        node = node_path[i]
        nof_parents = len(node.high_parents) + len(node.low_parents)
        if nof_parents > 1:
            copy_index = i
            break
    # Перенаправляем путь
    if copy_index != None:
        # Путь нужно скопировать для перенаправления
        RedirCopyPath_v1(copy_index, lit_path, node_path, diagram,node_paths)
        return True
    else:
        # Копирование не требуется
        RedirOriginalPath_v1(lit_path[-1],node_path[-1],diagram, node_paths)
        return False



def RedirCopyPath_v1(copy_index, lit_path, node_path, diagram,node_paths):
    old_nodes = node_path[copy_index:]
    old_lits = lit_path[copy_index:]
    redir_node = node_path[copy_index-1]
    redir_lit = lit_path[copy_index-1]
    copylink_pair = (node_path[copy_index-1], node_path[copy_index])
    #print('copylink pair', [(x.Value(),x) for x in copylink_pair])
    # Рекурсивно удаляем из таблицы узлы от последнего в пути наверх
    deleted_nodes = set()
    DeletingNodesFromTable(redir_node, diagram, deleted_nodes)
    # Копируем узлы и перенаправляем путь
    new_nodes = CopyNodes(redir_node, redir_lit, old_nodes, old_lits, diagram)
    # Работаем с copylink_pair в node_paths
    ReplaceCopyNodesInNodePaths(node_paths, new_nodes, old_nodes, copylink_pair)
    # Добавляем узлы в таблицу, проверяя склейку
    deleted_nodes.update(new_nodes)
    GluingNodes(deleted_nodes, diagram)



def RedirOriginalPath_v1(last_lit, last_node, diagram, node_paths):
    # Рекурсивно удаляем из таблицы узлы от последнего в пути наверх
    deleted_nodes = set()
    DeletingNodesFromTable(last_node,diagram, deleted_nodes)
    quest_leaf = diagram.GetQuestionLeaf()
    # Перенаправляем путь
    if last_lit < 0:
        for i in range(len(last_node.low_childs)):
            if last_node.low_childs[i] == diagram.GetQuestionLeaf():
                last_node.low_childs[i] = diagram.GetTrueLeaf()
                break
        quest_leaf.low_parents = [x for x in quest_leaf.low_parents if x is not last_node]
        diagram.GetTrueLeaf().low_parents.append(last_node)
    else:
        for i in range(len(last_node.high_childs)):
            if last_node.high_childs[i] == diagram.GetQuestionLeaf():
                last_node.high_childs[i] = diagram.GetTrueLeaf()
                break
        quest_leaf.high_parents = [x for x in quest_leaf.high_parents if x is not last_node]
        diagram.GetTrueLeaf().high_parents.append(last_node)
    # Проверяем ранее удаленные из таблицы узлы на склейку
    GluingNodes(deleted_nodes, diagram)


def GluingNodes_v1(deleted_nodes, diagram, node_paths):
    deleted_nodes = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_, deleted_nodes)
    for node in deleted_nodes:
        node.HashKey()
        if node.hash_key in diagram.table_ and diagram.table_[node.hash_key] is not node:
            it_node = diagram.table_[node.hash_key]
            if node is it_node:
                print('ERROR')
            #print('Glued node',(node.Value(), node),'with node',(it_node.Value(),it_node))
            GluingNode_v1(node,it_node, node_paths)
            del node
        else:
            diagram.table_[node.hash_key] = node


def GluingNode_v1(node,it_node, node_paths):
    # заменяем ссылки в родителях
    ReplaceParentsLinksToNode(node,it_node)
    # Удаляем ссылки потомков узла на него
    DeleteChildsLinksToNode(node)
    # Заменяем узел в node_paths
    ReplaceNodeInNodePaths(node,it_node,node_paths)