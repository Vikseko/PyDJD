from Utils import *
from Builder import DisjunctiveDiagramsBuilder
from Redirection import *

# Получаем КНФ из диаграммы (все пути из корней в терминальную 'true')
def GetCNFFromDiagram(diagram:DisjunctiveDiagram):
    cnf = []
    node_paths = []
    true_leaf = diagram.GetTrueLeaf()
    for node in true_leaf.high_parents:
        clause = []
        clause.append(node.var_id)
        node_path = []
        node_path.append(node)
        WritePaths(cnf,node_paths,node_path,clause)
    for node in true_leaf.low_parents:
        clause = []
        clause.append(-node.var_id)
        node_path = []
        node_path.append(node)
        WritePaths(cnf,node_paths,node_path,clause)
    NegateProblem(cnf)
    return cnf,node_paths

# Получаем ДНФ из диаграммы (все пути из корней в терминальную 'true')
def GetDNFFromDiagram(diagram:DisjunctiveDiagram):
    dnf = []
    node_paths = []
    true_leaf = diagram.GetTrueLeaf()
    for node in true_leaf.high_parents:
        clause = []
        clause.append(node.var_id)
        node_path = []
        node_path.append(node)
        WritePaths(dnf,node_paths,node_path,clause)
    for node in true_leaf.low_parents:
        clause = []
        clause.append(-node.var_id)
        node_path = []
        node_path.append(node)
        WritePaths(dnf,node_paths,node_path,clause)
    return dnf,node_paths

# Получаем false paths из диаграммы (все пути из корней в терминальную '?')
def GetQuestionPathsFromDiagram(diagram:DisjunctiveDiagram):
    question_paths = []
    node_paths = []
    question_leaf = diagram.GetQuestionLeaf()
    for node in question_leaf.high_parents:
        clause = []
        clause.append(node.var_id)
        node_path = []
        node_path.append(node)
        WritePaths(question_paths,node_paths,node_path,clause)
    for node in question_leaf.low_parents:
        clause = []
        clause.append(-node.var_id)
        node_path = []
        node_path.append(node)
        WritePaths(question_paths,node_paths,node_path,clause)
    return question_paths,node_paths

def WritePaths(problem,node_paths,node_path,clause):
    current_node:DiagramNode = node_path[-1]
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

# Получаем false paths из диаграммы (все пути из корней в терминальную '?')
"""идём по графу снизу вверх, как только дошли до корня, пометили как посещенный, 
в следующий раз дойдём до другого корня.
в таком случае появляется сложность, что до одного корня можно дойти разными путями, 
а тут он уже посещенный и проблема.
поэтому делаем такой мув: когда у вершины все верхние для неё вершины помечены как посещенные, 
мы помечаем посещенной саму вершину, а верхние вершины наоборот ставим как непосещенные 
и теперь к ним снова можно пройти, но только уже через другую вершину какуюнибудь.
критерий полного останова — терминальная вершина помечена как посещенная."""
def RedirectQuestionPathsFromDiagram(diagram:DisjunctiveDiagram):
    cnf, tmp_ = GetCNFFromDiagram(diagram)
    cnf = CNF(from_clauses=cnf)
    g = MapleChrono(bootstrap_with=cnf)
    #g.conf_budget(1000)
    question_leaf = diagram.GetQuestionLeaf()
    while not question_leaf.IsVisited():
        #print('\nSearch in progress')
        stop_flag = True
        finded_flag = False
        for node in question_leaf.high_parents:
            if not node.IsVisited() and not finded_flag:
                stop_flag = False
                clause = []
                clause.append(node.var_id)
                node_path = []
                node_path.append(node)
                finded_flag = RedirPaths(node_path,clause, g, diagram, finded_flag)
                if finded_flag:
                    continue
        for node in question_leaf.low_parents:
            if not node.IsVisited() and not finded_flag:
                stop_flag = False
                clause = []
                clause.append(-node.var_id)
                node_path = []
                node_path.append(node)
                finded_flag = RedirPaths(node_path,clause, g, diagram, finded_flag)
                if finded_flag:
                    continue
        if stop_flag == True:
            question_leaf.Visit()
    print('Number of question paths:'.ljust(30, ' '), diagram.question_path_count_)
    print('Number of not solved paths'.ljust(30, ' '),  diagram.question_path_count_ - (diagram.copy_redir + diagram.uniq_redir))
    print('Number of copy redirected'.ljust(30, ' '), diagram.copy_redir)
    print('Number of uniq redirected'.ljust(30, ' '), diagram.uniq_redir)


def RedirPaths(node_path,clause, g, diagram, finded_flag):
    current_node:DiagramNode = node_path[-1]
    if current_node.IsRoot():
        clause.reverse()
        node_path.reverse()
        diagram.question_path_count_ += 1
        #problem.append(clause)
        #node_paths.append(node_path)
        #print(clause)
        s, model = PathCheck(clause, g)
        if s == False:
            pass
            flag_copy_path = RedirectPath(clause, node_path, diagram)
            if flag_copy_path == True:
                diagram.copy_redir += 1
            else:
                diagram.uniq_redir += 1
        if s == None:
            pass
        if s == True:
            # print('Problem solved due false path checking.')
            # print('Model:', model)
            # break
            pass
        current_node.Visit()
        return True
    else:
        visited_flag = True
        for node in itertools.chain(current_node.high_parents, current_node.low_parents):
            if not node.IsVisited():
                visited_flag = False
        if visited_flag == True:
            current_node.Visit()
            for node in itertools.chain(current_node.high_parents, current_node.low_parents):
                node.UnVisit()
        if not current_node.Visit():
            for node in current_node.high_parents:
                if not node.IsVisited() and not finded_flag:
                    hclause = copy.copy(clause)
                    hnode_path = copy.copy(node_path)
                    hclause.append(node.var_id)
                    hnode_path.append(node)
                    finded_flag = RedirPaths(hnode_path, hclause, g, diagram, finded_flag)
                    if finded_flag:
                        return True
            for node in current_node.low_parents:
                if not node.IsVisited() and not finded_flag:
                    lclause = copy.copy(clause)
                    lnode_path = copy.copy(node_path)
                    lclause.append(-node.var_id)
                    lnode_path.append(node)
                    finded_flag = RedirPaths(lnode_path, lclause, g, diagram, finded_flag)
                    if finded_flag:
                        return True
