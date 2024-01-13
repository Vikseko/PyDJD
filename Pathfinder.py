import os

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
    cnf = NegateProblem(cnf)
    return cnf, node_paths

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
        CountPaths(node_path, clause, paths_table)
    for node in question_leaf.low_parents:
        clause = []
        clause.append(-node.var_id)
        node_path = []
        node_path.append(node)
        CountPaths(node_path, clause, paths_table)
    return paths_table


def CountPaths(node_path,clause,paths_table):
    current_node:DiagramNode = node_path[-1]
    if current_node.IsRoot():
        clause.sort(key=abs)
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


def SolvePaths(problem, all_question_pathes, order, timelimit=0, numproc=1):
    cnf = CNF(from_clauses=problem)
    paths = [sorted(list(path), key=lambda x: order.index(abs(x))) for path in all_question_pathes]
    unsats = 0
    sats = 0
    new_clauses = []
    solve_times = []
    indet_paths = []
    first_sat_time = None
    models = set()
    start_clauses_checking = time.time()
    results = []
    print('Number of paths before finding timelimit:', len(paths))
    g = MapleChrono(bootstrap_with=cnf)
    if timelimit < 0:
        print('Get negative value of timelimit:', timelimit)
        inittimelimit = abs(timelimit)
        results, paths, new_clauses, timelimit, first_sat_time, models, sats, unsats = FindGoodTimelimitForPaths(g, paths, order,
                                                                                          start_clauses_checking, inittimelimit)
    print('\nTimelimit:', timelimit)
    if numproc < 2:
        for index, assumption in enumerate(paths):
            st_time_ = time.time()
            print('Path {} of {}: {}'.format(index + 1, len(paths), assumption), end='')
            if timelimit == 0:
                s, model = SolvePath(assumption, g)
            else:
                s, model = SolvePathTimelimit(assumption, g, timelimit)
            end_time_ = round(time.time() - st_time_, 3)
            solve_times.append(end_time_)
            results.append([assumption, s, end_time_])
            if s is False:
                unsats += 1
                new_clauses.append([-x for x in assumption])
                print(' ---> {}, {} s.'.format(s, end_time_))
            elif s is None:
                # print('SAT-oracle says None. Go next path.')
                print(' ---> {}, {} s.'.format(s, end_time_))
                indet_paths.append(assumption)
            elif s:
                sats += 1
                print(' ---> {}, {} s.'.format(s, end_time_))
                if sats == 1 and first_sat_time is None:
                    first_sat_time = time.time() - start_clauses_checking
                print('Problem solved due false path checking.')
                model.sort(key=lambda x: order.index(abs(x)))
                print('Model:', model)
                models.add(tuple(model))
    else:
        print('Number of processes', numproc)
        enum_paths = list(enumerate(paths))
        sats_, unsats_, results_, models_, new_clauses_, indet_paths_, solve_flag = PathsSolvingTimelimit_mp(enum_paths, numproc, cnf, timelimit)
        sats += sats_
        unsats += unsats_
        results.extend(results_)
        if models_:
            models.update(models_)
        new_clauses.extend(new_clauses_)
        indet_paths.extend(indet_paths_)
        solve_times = [x[2] for x in results]
    print('\nResults (sorted):')
    print(*sorted(results, key=lambda x: (x[2], x[0])), sep='\n')
    if models:
        print('Number of paths:'.ljust(30, ' '), len(all_question_pathes))
        print('Number of UNSAT paths:'.ljust(30, ' '), unsats)
        print('Number of SAT paths:'.ljust(30, ' '), len(all_question_pathes)-unsats)
        print('Time to first SAT:'.ljust(30, ' '), first_sat_time)
        print('Models:')
        print(*models, sep='\n')
    elif unsats == len(all_question_pathes):
        print('UNSAT was proved for whole subfunction.')
        print('Number of paths:'.ljust(30, ' '), len(all_question_pathes))
        print('Number of UNSAT paths:'.ljust(30, ' '), unsats)
    else:
        print('Part of paths was solved.')
        print('Number of paths:'.ljust(30, ' '), len(all_question_pathes))
        print('Number of UNSAT paths:'.ljust(30, ' '), unsats)
    print('Paths solving total time:'.ljust(30, ' '), time.time() - start_clauses_checking)
    print('Paths solving times (20 longest):'.ljust(30, ' '), sorted(solve_times, reverse=True)[:min(20, len(solve_times))])
    print('Average solving time:'.ljust(30, ' '), round(mean(solve_times), 3))
    print('Number of new clauses:'.ljust(30, ' '), unsats)
    print('Number of indeterminate paths:', len(indet_paths))
    if sats > 0:
        solve_flag = True
    elif unsats == len(all_question_pathes):
        solve_flag = True
    else:
        solve_flag = False
    return new_clauses, indet_paths, solve_flag, timelimit


def FindGoodTimelimitForPaths(solver, paths, order, start_clauses_checking, inittimelimit):
    timelimit = inittimelimit
    first_sat_time = None
    sample_size = min(max(len(paths)//100, 10), len(paths))
    solved = 0
    results = []
    new_clauses = []
    sats = 0
    unsats = 0
    models = set()
    border = int((sample_size/100)*90)
    print('\nStart finding good timelimit.')
    print('Total number of paths:', len(paths))
    print('Sample size:', sample_size)
    print('Solved border:', border)
    while solved < border:
        print('\nCurrent timelimit:', timelimit)
        solved = 0
        if len(paths) > sample_size:
            sample = [paths.pop(random.randrange(len(paths))) for _ in range(sample_size)]
        else:
            sample = paths
            paths = []
        for assumption in sample:
            st_time_ = time.time()
            print('Path from sample: {}'.format(assumption), end='')
            s, model = SolvePathTimelimit(assumption, solver, timelimit)
            end_time_ = round(time.time() - st_time_, 3)
            if s is False:
                unsats += 1
                solved += 1
                new_clauses.append([-x for x in assumption])
                print(' ---> {}, {} s.'.format(s, end_time_))
                results.append([assumption, s, end_time_])
            elif s is None:
                # print('SAT-oracle says None. Go next path.')
                print(' ---> {}, {} s.'.format(s, end_time_))
                paths.append(assumption)
            elif s:
                sats += 1
                solved += 1
                print(' ---> {}, {} s.'.format(s, end_time_))
                if sats == 1:
                    first_sat_time = time.time() - start_clauses_checking
                print('Problem solved due timelimit finding checking.')
                model.sort(key=lambda x: order.index(abs(x)))
                print('Model:', model)
                models.add(tuple(model))
                results.append([assumption, s, end_time_])
        print('Solved:', solved)
        print('Number of remain paths:', len(paths))
        if solved < border:
            timelimit += max(1, int(timelimit/5+1), int((timelimit / 2)*((100-(solved/sample_size*100))//10)))
    return results, paths, new_clauses, timelimit, first_sat_time, models, sats, unsats

def SolvePath(lit_path, solver):
    # timer = Timer(0.01, interrupt, [solver])
    # timer.start()
    # s = solver.solve_limited(assumptions=lit_path, expect_interrupt=True)
    # solver.clear_interrupt()
    # timer.cancel()
    s = solver.solve(assumptions=lit_path)
    if s is None:
        return s, None
    elif s is False:
        return s, None
    elif s:
        model = solver.get_model()
        return s, model


def SolvePathTimelimit(lit_path, solver, timelimit):
    timer = Timer(timelimit, interrupt, [solver])
    timer.start()
    s = solver.solve_limited(assumptions=lit_path, expect_interrupt=True)
    solver.clear_interrupt()
    timer.cancel()
    if s is None:
        return s, None
    elif s is False:
        return s, None
    elif s:
        model = solver.get_model()
        return s, model


def GetPathsToFalse_ddformat(logpath, bdd_root, bdd_manager):
    question_paths = set()
    tmp_name_ = str(os.getpid()) + '_' + str(bdd_root.var) + '_tmpbddforpaths.json'
    bdd_manager.dump(logpath + tmp_name_, roots=[bdd_root])
    bdd_dict = json.load(open(logpath + tmp_name_, 'r'))
    levels_vars_dict = {v: k for k, v in bdd_dict['level_of_var'].items()}
    root_node_id = abs(bdd_dict['roots'][0])
    root_node = bdd_dict[str(root_node_id)]
    multiplier = 0 if bdd_dict['roots'][0] > 0 else 1
    init_clause = []
    WritePaths_dd(levels_vars_dict, bdd_dict, init_clause, root_node, question_paths, multiplier)
    # negate_root = bdd_manager.add_expr(r'!{u}'.format(u=bdd_root))
    # bdd_manager.collect_garbage()
    # for index_assign, d in enumerate(bdd_manager.pick_iter(negate_root)):
    #     print(index_assign, d)
    return question_paths


def WritePaths_dd(levels_vars_dict, bdd_dict, clause, node, question_paths, multiplier):
    node_level = node[0]
    node_var = int(levels_vars_dict[node_level][1:])
    neg_clause = clause + [-1 * node_var]
    if node[1] == 'F':
        if multiplier % 2 == 0:
            neg_clause.sort(key=abs)
            question_paths.add(tuple(neg_clause))
            # print('Final neg clause, from F:', neg_clause)
    elif node[1] == 'T':
        if multiplier % 2 == 1:
            neg_clause.sort(key=abs)
            question_paths.add(tuple(neg_clause))
            # print('Final neg clause, from T:', neg_clause)
    else:
        neg_child = bdd_dict[str(abs(node[1]))]
        if node[1] < 0:
            neg_multiplier = multiplier + 1
        else:
            neg_multiplier = multiplier
        WritePaths_dd(levels_vars_dict, bdd_dict, neg_clause, neg_child, question_paths, neg_multiplier)
    pos_clause = clause + [node_var]
    if node[2] == 'F':
        if multiplier % 2 == 0:
            pos_clause.sort(key=abs)
            question_paths.add(tuple(pos_clause))
            # print('Final pos clause, from F:', pos_clause)
    elif node[2] == 'T':
        if multiplier % 2 == 1:
            pos_clause.sort(key=abs)
            question_paths.add(tuple(pos_clause))
            # print('Final pos clause, from T:', pos_clause)
    else:
        pos_child = bdd_dict[str(abs(node[2]))]
        if node[2] < 0:
            pos_multiplier = multiplier + 1
        else:
            pos_multiplier = multiplier
        WritePaths_dd(levels_vars_dict, bdd_dict, pos_clause, pos_child, question_paths, pos_multiplier)


def PathsSolvingTimelimit_mp(enum_paths, numproc, cnf, tlim):
    new_clauses = []
    next_iter_paths = []
    sats = 0
    unsats = 0
    results = []
    parts_q_pathes = chunks(enum_paths, round_up(len(enum_paths) / numproc))
    nof_paths = len(enum_paths)
    p = multiprocessing.Pool(numproc)
    jobs = [p.apply_async(PathSolvingTimelimit_mp, (part, cnf, tlim, nof_paths)) for part in parts_q_pathes]
    model = None
    solved = False
    for job in jobs:
        result = job.get()
        if (len(result) == 3) and (result[0] == 'True'):
            solved = True
            model = result[1]
            break
        else:
            new_clauses.extend(result[0])
            next_iter_paths.extend(result[1])
            sats += result[2]
            unsats += result[3]
            results.extend(result[4])
    p.close()
    p.join()
    return sats, unsats, results, model, new_clauses, next_iter_paths, solved


def PathSolvingTimelimit_mp(part, cnf, timelim, nof_paths):
    solver = MapleChrono(bootstrap_with=cnf)
    new_clauses = []
    indet_paths = []
    results = []
    sats = 0
    unsats = 0
    for counter, assumption in part:
        timer = Timer(timelim, interrupt, [solver])
        timer.start()
        start_time = time.time()
        s = solver.solve_limited(assumptions=assumption, expect_interrupt=True)
        solver.clear_interrupt()
        timer.cancel()
        print('Path {} of {}: {} ---> {}, {} s.'.format(counter, nof_paths, assumption, s, time.time() - start_time))
        if s is None:
            indet_paths.append(assumption)
            results.append([assumption, s, time.time() - start_time])
        elif s is False:
            unsats += 1
            new_clauses.append([-x for x in assumption])
            results.append([assumption, s, time.time() - start_time])
        elif s is True:
            sats += 1
            model = solver.get_model()
            results.append([assumption, s, time.time() - start_time])
            return ['True', model, log]
    #q.put(new_clauses)
    return [new_clauses, indet_paths, sats, unsats, results]


def CheckPaths_mp(diagram, all_question_pathes, numproc, timelim, rounds=1):
    cnf, tmp_ = GetCNFFromDiagram(diagram)
    start_clauses_checking = time.time()
    question_paths_for_check = copy.copy(all_question_pathes)
    solved = False
    for i in range(rounds):
        new_clauses = []
        next_iter_paths = []
        parts_q_pathes = chunks(question_paths_for_check, round_up(len(question_paths_for_check)/numproc))
        print()
        print('Start round', i)
        print('Current number of paths to check:', len(question_paths_for_check))
        p = multiprocessing.Pool(numproc)
        jobs = [p.apply_async(PathesCheck_mp, (part, cnf, timelim)) for part in parts_q_pathes]
        model = None
        for job in jobs:
            result = job.get()
            if (len(result) == 2) and (result[0] == 'True'):
                solved = True
                model = result[1]
                break
            else:
                new_clauses.extend(result[0])
                next_iter_paths.extend(result[1])
        p.close()
        p.join()
        print('Checking paths complete.')
        if solved == True:
            print('Problem was solved.')
            print('Model:', model)
            break
        else:
            cnf.extend(new_clauses)
            print('Complete iteration:', i)
            print('Number of new clauses:'.ljust(30,' '), len(new_clauses))
            if len(next_iter_paths) < 2:
                print('No more question paths to check.')
                print('Total DJD-prep time:', time.time() - start_clauses_checking)
                break
            if i == rounds - 1:
                print('Total DJD-prep time:', time.time() - start_clauses_checking)
            else:
                # v1
                # chunks_paths = list(chunks(next_iter_paths, 2))
                # if len(chunks_paths[-1]) < 2:
                #    chunks_paths[-1] = [next_iter_paths[-2], next_iter_paths[-1]]
                # question_paths_for_check = [sorted(list(set(flatten(pair))), key = abs) for pair in chunks_paths]
                # v2
                # chunks_paths = list(make_pairs(random.sample(next_iter_paths, int(len(next_iter_paths)/100)), random.sample(next_iter_paths, int(len(next_iter_paths)/100))))
                # v3
                question_paths_for_check = next_iter_paths
                print('Current DJD-prep time:', time.time() - start_clauses_checking)
    cnf = CNF(from_clauses=cnf)
    return cnf, new_clauses


def PathesCheck_mp(part_lit_paths, cnf, timelim):
    cnf = CNF(from_clauses=cnf)
    solver = MapleChrono(bootstrap_with=cnf)
    new_clauses = []
    indet_paths = []
    counter = 0
    for lit_path in part_lit_paths:
        counter += 1
        #print('hi', counter, lit_path)
        timer = Timer(timelim, interrupt, [solver])
        timer.start()
        s = solver.solve_limited(assumptions = lit_path, expect_interrupt=True)
        solver.clear_interrupt()
        #timer.cancel()
        if s == None:
            #print('true')
            indet_paths.append(lit_path)
            continue
        elif s == False:
            #print('true')
            new_clauses.append([-x for x in lit_path])
        elif s == True:
            #print('true')
            model = solver.get_model()
            return ['True', model]
    #q.put(new_clauses)
    return [new_clauses, indet_paths]


def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield tuple(lst[i:i + n])


def round_up(number): return int(number) + (number % 1 > 0)


def flatten(l):
    return [item for sublist in l for item in sublist]


def make_pairs(*lists):
    for t in combinations(lists, 2):
        for pair in product(*t):
            yield pair
