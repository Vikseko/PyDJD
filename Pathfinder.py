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


# Считаем question paths в диаграмме (все пути из корней в терминальную '?')
def CountQuestionPathsInDiagram(diagram:DisjunctiveDiagram):
    paths_table = set()
    question_leaf = diagram.GetQuestionLeaf()
    for node in question_leaf.high_parents:
        clause = []
        clause.append(node.var_id)
        node_path = []
        node_path.append(node)
        CountPaths(node_path,clause,paths_table)
    for node in question_leaf.low_parents:
        clause = []
        clause.append(-node.var_id)
        node_path = []
        node_path.append(node)
        CountPaths(node_path,clause,paths_table)
    return paths_table


def CountPaths(node_path,clause,paths_table):
    current_node:DiagramNode = node_path[-1]
    if current_node.IsRoot():
        clause.reverse()
        clause.sort()
        paths_table.add(tuple(clause))
    else:
        for node in current_node.high_parents:
            hclause = copy.copy(clause)
            hnode_path = copy.copy(node_path)
            hclause.append(node.var_id)
            hnode_path.append(node)
            CountPaths(hnode_path, hclause,paths_table)
        for node in current_node.low_parents:
            lclause = copy.copy(clause)
            lnode_path = copy.copy(node_path)
            lclause.append(-node.var_id)
            lnode_path.append(node)
            CountPaths(lnode_path, lclause,paths_table)

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
        if not s:
            flag_copy_path = RedirectPath(clause, node_path, diagram)
            if flag_copy_path:
                diagram.copy_redir += 1
            else:
                diagram.uniq_redir += 1
        if s is None:
            pass
        if s:
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
        if visited_flag:
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


def RedirectQuestionPathsFromDiagram_v3(diagram:DisjunctiveDiagram, question_paths_count):
    cnf, tmp_ = GetCNFFromDiagram(diagram)
    cnf = CNF(from_clauses=cnf)
    g = MapleChrono(bootstrap_with=cnf)
    #g.conf_budget(1000)
    question_leaf = diagram.GetQuestionLeaf()
    clauses_set = set()
    while not question_leaf.IsVisited():
        #print('\nSearch in progress')
        finded_flag = False
        if diagram.question_path_count_ % 2 == 0:
            for node in question_leaf.high_parents:
                if not finded_flag:
                    clause = []
                    clause.append(node.var_id)
                    node_path = []
                    node_path.append(node)
                    finded_flag = RedirPaths_v3(node_path,clause, g, diagram, finded_flag,clauses_set, question_paths_count)
                    if finded_flag:
                        break
            if finded_flag == True:
                continue
            for node in question_leaf.low_parents:
                if not finded_flag:
                    clause = []
                    clause.append(-node.var_id)
                    node_path = []
                    node_path.append(node)
                    finded_flag = RedirPaths_v3(node_path,clause, g, diagram, finded_flag,clauses_set, question_paths_count)
                    if finded_flag:
                        break
        else:
            for node in reversed(question_leaf.low_parents):
                if not finded_flag:
                    clause = []
                    clause.append(-node.var_id)
                    node_path = []
                    node_path.append(node)
                    finded_flag = RedirPaths_v3(node_path,clause, g, diagram, finded_flag,clauses_set, question_paths_count)
                    if finded_flag:
                        break
            if finded_flag == True:
                continue
            for node in reversed(question_leaf.high_parents):
                if not finded_flag:
                    clause = []
                    clause.append(node.var_id)
                    node_path = []
                    node_path.append(node)
                    finded_flag = RedirPaths_v3(node_path,clause, g, diagram, finded_flag,clauses_set, question_paths_count)
                    if finded_flag:
                        break
        if finded_flag == False:
            question_leaf.Visit()
    #print('Number of question paths:'.ljust(30, ' '), diagram.question_path_count_)
    print('Number of solved paths'.ljust(30, ' '),  diagram.copy_redir + diagram.uniq_redir)
    print('Number of copy redirected'.ljust(30, ' '), diagram.copy_redir)
    print('Number of uniq redirected'.ljust(30, ' '), diagram.uniq_redir)


def RedirPaths_v3(node_path,clause, g, diagram, finded_flag,clauses_set, question_paths_count):
    current_node:DiagramNode = node_path[-1]
    if current_node.IsRoot():
        clause.reverse()
        if tuple(sorted(clause)) not in clauses_set:
            clauses_set.add(tuple(sorted(clause)))
            node_path.reverse()
            diagram.question_path_count_ += 1
            #sys.stdout.write("Checking path %s of %s\r" % (diagram.question_path_count_,question_paths_count))
            #sys.stdout.flush()
            #print('Find new path: ',clause)
            s, model = PathCheck(clause, g)
            if s == False:
                #print('SAT-oracle says False. Redirect path.')
                flag_copy_path = RedirectPath(clause, node_path, diagram)
                if flag_copy_path == True:
                    diagram.copy_redir += 1
                else:
                    diagram.uniq_redir += 1
            if s == None:
                #print('SAT-oracle says None. Go next path.')
                return False
            if s == True:
                #print('Problem solved due false path checking.')
                #print('Model:', model)
                # break
                pass
            #current_node.Visit()
            return True
        else:
            #print('Finded path is already in table, go next: ', clause)
            return False
    else:
        for node in current_node.high_parents:
            if not finded_flag:
                hclause = copy.copy(clause)
                hnode_path = copy.copy(node_path)
                hclause.append(node.var_id)
                hnode_path.append(node)
                finded_flag = RedirPaths_v3(hnode_path, hclause, g, diagram, finded_flag,clauses_set, question_paths_count)
                if finded_flag:
                    return True
        for node in current_node.low_parents:
            if not finded_flag:
                lclause = copy.copy(clause)
                lnode_path = copy.copy(node_path)
                lclause.append(-node.var_id)
                lnode_path.append(node)
                finded_flag = RedirPaths_v3(lnode_path, lclause, g, diagram, finded_flag,clauses_set, question_paths_count)
                if finded_flag:
                    return True
        return False


def CheckPaths(diagram, all_question_pathes):
    cnf, tmp_ = GetCNFFromDiagram(diagram)
    cnf = CNF(from_clauses=cnf)
    g = MapleChrono(bootstrap_with=cnf)
    new_clauses_counter = 0
    new_clauses = []
    start_clauses_checking = time.time()
    for clause in all_question_pathes:
        s, model = PathCheck(clause, g)
        if s == False:
            # print('SAT-oracle says False. Redirect path.')
            new_clauses_counter += 1
            new_clauses.append([-x for x in clause])
        if s == None:
            # print('SAT-oracle says None. Go next path.')
            pass
        if s == True:
            # print('Problem solved due false path checking.')
            # print('Model:', model)
            # break
            pass
    #print('Paths checking time:'.ljust(30, ' '), time.time() - start_clauses_checking)
    cnf.extend(new_clauses)
    print('Number of new clauses:'.ljust(30,' '), new_clauses_counter)
    return cnf

def SortClausesInCnf(cnf):
    for clause in cnf:
        clause.sort(key=lambda x: abs(x))
    cnf.sort(key = cmp_to_key(SortClauses))
    return cnf

def SortClauses(clause1, clause2):
    minlen = min(len(clause1),len(clause2))
    for i in range(minlen):
        if abs(clause1[i]) > abs(clause2[i]):
            return 1
        elif abs(clause1[i]) < abs(clause2[i]):
            return -1
    for i in range(minlen):
        if clause1[i] > clause2[i]:
            return 1
        elif clause1[i] < clause2[i]:
            return -1
    return 0