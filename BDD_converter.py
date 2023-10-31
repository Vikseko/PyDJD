import multiprocessing
import pprint

from Pathfinder import *
from Intervals import *
import pysat
from pysat.solvers import MapleChrono
from pysat.formula import CNF
# from Draw import *
import gc

from Types import DiagramNode
import queue


def DJDtoBDD_separated(diagrams, numproc, order):
    current_djd_diagrams = diagrams
    counter = 0
    sys.setrecursionlimit(100000)
    iter_times = []
    conjoin_times = []
    unsat_flag = False
    # переводим каждую поддиаграмму в бдд
    current_bdd_diagrams, subdjd_to_bdd_times = DJDstoBDDs(diagrams, numproc)
    current_bdd_diagrams = sorted(current_bdd_diagrams, key=lambda x: order.index(abs(x.main_root_.Value())))
    for index, diagram in enumerate(current_bdd_diagrams):
        # diagram.PrintProblem()
        diagram.PrintCurrentTable('SubBDDiagram ' + str(index + 1) + ':')
        if diagram.VertexCount() == 0:
            print('Empty BDD is obtained. Initial CNF in unsatisfiable.')
            unsat_flag = True
    nof_link_actions_djd2bdd = sum(x.actions_with_links_ for x in current_bdd_diagrams)
    print('Actions with links after subdiagrams transformations:', nof_link_actions_djd2bdd)
    # попарно объединяем поддиаграммы пока не останется одна финальная диаграмма
    while len(current_bdd_diagrams) > 1 and not unsat_flag:
        current_bdd_diagrams = sorted(current_bdd_diagrams, key=lambda x: order.index(abs(x.main_root_.Value())))
        # print('order:', order)
        # print('sorted diagrams by roots:', [x.main_root_.Value() for x in current_bdd_diagrams])
        roots_sorted_diagrams = [x.main_root_.Value() for x in current_bdd_diagrams]
        # print('sizes of diagrams:', [x.VertexCount() for x in current_bdd_diagrams])
        sizes_of_diagrams = [x.VertexCount() for x in current_bdd_diagrams]
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
        print('\n\nCurrent iteration:', counter)
        print('Number of processes:', (min(len(diagrams_pairs), numproc)))
        print('Number of subdiagrams:', current_nof_diagrams)
        print('Number of tasks (pairs):', len(diagrams_pairs))
        print('Order:', order)
        print('Sorted diagrams by roots:', roots_sorted_diagrams)
        print('Sizes of diagrams:', sizes_of_diagrams)
        # print('Pairs:', diagrams_pairs)
        conjoin_times_iter = []
        if numproc == 1:
            for pair in diagrams_pairs:
                new_diagram, conjoin_time, log_lines = ConjoinBDDs((pair[0], pair[1]))
                next_iter_diagrams.append(new_diagram)
                conjoin_times_iter.append(conjoin_time)
                print(*log_lines, sep='\n')
                if new_diagram.VertexCount() == 0:
                    print('Empty diagram obtained. Initial CNF in unsatisfiable.')
                    unsat_flag = True
                    break
        else:
            with multiprocessing.Pool(min(numproc, len(diagrams_pairs))) as p:
                for result in p.map(ConjoinBDDs, [(pair[0], pair[1]) for pair in diagrams_pairs]):
                    new_diagram = result[0]
                    conjoin_time = result[1]
                    log_lines = result[2]
                    print('Job finished.')
                    print(*log_lines, sep='\n')
                    next_iter_diagrams.append(new_diagram)
                    conjoin_times_iter.append(conjoin_time)
                    if new_diagram.VertexCount() == 0:
                        print('Empty diagram obtained. Initial CNF in unsatisfiable.')
                        unsat_flag = True
        iter_time = time.time() - iter_start_time
        iter_times.append(iter_time)
        conjoin_times.append(conjoin_times_iter)
        if not unsat_flag:
            current_bdd_diagrams = next_iter_diagrams
        else:
            current_bdd_diagrams = [x for x in next_iter_diagrams if x.VertexCount() == 0]
    final_diagram = current_bdd_diagrams[0]
    EnumerateBDDiagramNodes(final_diagram)
    print('Times for initial transformations', [round(x, 3) for x in subdjd_to_bdd_times])
    print('Sum of times for initial transformations', round(sum(subdjd_to_bdd_times), 3))
    print('Times for iterations', [round(x, 3) for x in iter_times])
    print('Sum of times for iterations:', round(sum(iter_times), 3))
    print('Times for conjoins by iteration:', [[round(y, 3) for y in x] for x in conjoin_times])
    print('Sum of times for conjoins by iteration:', round(sum([sum(x) for x in conjoin_times]), 3))
    return final_diagram, nof_link_actions_djd2bdd


def DJDtoBDD_pbi_separated(djds, pbi_bdds, numproc, order, logpath):
    counter = 0
    sys.setrecursionlimit(100000)
    iter_times = []
    conjoin_times = []
    unsat_flag = False
    fun_bdds, subdjd_to_bdd_times = DJDstoBDDs(djds, numproc)
    for index, diagram in enumerate(fun_bdds):
        # diagram.PrintProblem()
        diagram.PrintCurrentTable('SubBDDiagram ' + str(index + 1) + ':')
        if diagram.VertexCount() == 0:
            print('Empty BDD is obtained. Initial CNF in unsatisfiable.')
            unsat_flag = True
    if not unsat_flag:
        alg_ver = False
        if alg_ver:
            # Версия, использующая реализацию apply для нашего формата диаграмм
            for pbi_bdd in pbi_bdds:
                # TODO
                # Тут нам нужен алгоритм апплай.
                # Берём наши диаграммы, приклеиваем к ним алгоритмом апплай интервалы (к первой к примеру),
                # к каждой второй к примеру, потом склеиваем попарно как раньше
                # Второй вариант: приклеиваем их по алгоритму избавления от небинарностей
                pass
        else:
            bdd_manager, times_for_pbi = gluing_sep_BDD(fun_bdds, pbi_bdds, order, logpath)
            return bdd_manager, times_for_pbi


def gluing_sep_BDD(fun_bdds, pbi_bdds, order, logpath, alg_ver=False):
    if alg_ver:
        # Версия, использующая реализацию apply для нашего формата диаграмм
        for pbi_bdd in pbi_bdds:
            # TODO
            # Тут нам нужен алгоритм апплай.
            # Берём наши диаграммы, приклеиваем к ним алгоритмом апплай интервалы (к первой к примеру),
            # к каждой второй к примеру, потом склеиваем попарно как раньше
            # Второй вариант: приклеиваем их по алгоритму избавления от небинарностей
            pass
    else:
        # Версия, использующая пакет dd
        vars_names = [str(x) for x in order if ((x != '?') and (x != 'true'))]
        vars_for_declare = ['x' + x for x in reversed(vars_names)]
        bdd_manager = BDD()
        bdd_manager.declare(*vars_for_declare)
        pbi_flag = True if pbi_bdds is not None else False
        pid = os.getpid()
        times_for_pbi = []
        times_for_fun = []
        max_sizes = []
        indices_unsat = []
        final_root = None
        if pbi_flag:
            pbi_dd_bdds = mybdds2ddbdds(pbi_bdds, bdd_manager, False, logpath + str(pid) + 'pbibdd')
            print('Nof dd PBI bdds', len(pbi_dd_bdds))
            pbi_sizes = [x.dag_size for x in pbi_dd_bdds]
            fun_bdds = mybdds2ddbdds(fun_bdds, bdd_manager, True, logpath + str(pid) + 'funbdd')
        else:
            pbi_dd_bdds = pbi_sizes = [None]
            fun_bdds = mybdds2ddbdds(fun_bdds, bdd_manager, False, logpath + str(pid) + 'funbdd')
        print('Nof dd functions\'s bdds', len(fun_bdds))
        fun_sizes = [x.dag_size for x in fun_bdds]
        final_roots = []
        for index, pbi_root in enumerate(pbi_dd_bdds):
            pbi_start_time = time.time()
            times_for_currentfun = []
            print('\nStart applying interval', index)
            if pbi_root is None:
                max_size = 0
            else:
                current_root = bdd_manager.add_expr(r'!{u}'.format(u=pbi_root))
                max_size = current_root.dag_size
            for fun_index, fun_root in enumerate(fun_bdds):
                if not pbi_flag and fun_index == 0:
                    current_root = fun_root
                    max_size = current_root.dag_size
                    continue
                fun_start_time = time.time()
                log_str = 'AND. PBI ' + str(index) + '. SubBDD ' + str(fun_index) + ' of ' + str(len(fun_bdds)) + '.'
                print(log_str, 'Size of current BDD before apply:', current_root.dag_size)
                print(log_str, 'Size of function BDD to apply:', fun_root.dag_size)
                if fun_root.dag_size > max_size:
                    max_size = fun_root.dag_size
                if pbi_flag:
                    pbi_fun_subbdd_root = bdd_manager.apply('and', current_root, fun_root)
                else:
                    pbi_fun_subbdd_root = bdd_manager.apply('or', current_root, fun_root)
                bdd_manager.collect_garbage()
                print(log_str, 'Size of current BDD after apply:', pbi_fun_subbdd_root.dag_size)
                fun_end_time = time.time()
                times_for_currentfun.append(fun_end_time - fun_start_time)
                current_root = pbi_fun_subbdd_root
                # print(current_root)
                if current_root.dag_size > max_size:
                    max_size = current_root.dag_size
                if current_root.dag_size == 1:
                    unsat_flag = True
                    # assert bdd_manager.to_expr(current_root) == 'FALSE', 'ERROR. Diagram is not FALSE.'
                    print(bdd_manager.to_expr(current_root))
                    print('Proved UNSAT for', index, 'interval, while applying interval by and.')
                    indices_unsat.append(fun_index + 1)
                    break
            print('Assignments for negated root (SAT assignments for initial CNF)', index, end=':\n')
            if pbi_flag:
                current_root_neg = current_root
            else:
                current_root_neg = bdd_manager.add_expr(r'!{u}'.format(u=current_root))
            print(current_root_neg)
            bdd_manager.collect_garbage()
            for index_assign, d in enumerate(bdd_manager.pick_iter(current_root_neg)):
                print(index_assign, d)
                if index_assign >= 100:
                    print('and others...')
                    break
            print('Number of significant vertices:', current_root.dag_size)
            final_roots.append(current_root)
            max_sizes.append(max_size)
            pbi_end_time = time.time()
            times_for_fun.append(times_for_currentfun)
            times_for_pbi.append(pbi_end_time - pbi_start_time)
            bdd_manager.collect_garbage()
        print()
        print('Final. Separated transition to BDD with PBI is complete.')
        print('Final. Initial number of DJDs:', len(fun_bdds))
        print('Final. PBI BDDs sizes:', pbi_sizes)
        print('Final. Function subbdds sizes:', fun_sizes)
        print('Final. Max sizes by intervals:', max_sizes)
        print('Final. Absolute max size:', max(max_sizes))
        print('Final. Funbdds indices causing graph elimination:', indices_unsat)
        print('Final. Total time for applying:', round(sum(times_for_pbi), 2))
        print('Final. Times for check intervals:', [round(x, 2) for x in times_for_pbi])
        return bdd_manager, times_for_pbi


def DJDtoBDD_separated_dd_package_only(problem, order, problem_comments, nof_intervals, problem_type='DNF'):
    # создаём подпроблемы, сортируем соответвенно порядку: первой идёт диаграмма, чем корень на 0 уровне
    # такая сортировка нужна чтобы склеивать их с интервалами, начиная с первой диаграммы
    start_construct_time = time.time()
    sys.setrecursionlimit(100000)
    fun_problems = SortProblems(DivideProblem(problem, order), order)
    pbi_problems = CreatePBIproblems(problem_comments, nof_intervals)
    pbi_flag = True if pbi_problems is not None else False
    vars_names = [str(x) for x in order if ((x != '?') and (x != 'true'))]
    vars_for_declare = ['x' + x for x in reversed(vars_names)]
    bdd_manager = BDD()
    bdd_manager.declare(*vars_for_declare)
    fun_bdds_roots, fun_bdds_max_sizes = Problems2BDD_dd_format(fun_problems, bdd_manager, problem_type)
    fun_bdds_sizes = [root.dag_size for root in fun_bdds_roots]
    print('Number of subbdds:', len(fun_bdds_roots))
    print('Construction time:', round(time.time() - start_construct_time, 2))
    pbi_bdds_sizes = [None]
    pbi_bdds_max_sizes = [None]
    indices_unsat = []
    bdd_max_sizes = []
    times_for_intervals = []
    final_roots = []
    if pbi_flag:
        # pbi_bdds_roots = Problems2BDD_dd_format(pbi_problems, bdd_manager, 'CNF')
        pbi_bdds_sizes = []
        pbi_bdds_max_sizes = []
        for pbi_index, pbi_problem in enumerate(pbi_problems):
            pbi_start_time = time.time()
            pbi_root, pbi_bdd_max_size = Problem2BDD_dd_format(pbi_problem, bdd_manager, 'CNF')
            pbi_bdds_max_sizes.append(pbi_bdd_max_size)
            pbi_bdds_sizes.append(pbi_root.dag_size)
            print('\nStart applying interval', pbi_index, 'to subbdds.')
            print('PBI BDD root:', pbi_root.var)
            bdd_max_size = 0
            unsat_flag = False
            current_root = pbi_root
            for fun_index, fun_root in enumerate(fun_bdds_roots):
                if problem_type == 'DNF':
                    log_str = 'APPLY OR. PBI ' + str(pbi_index) + '. SubBDD ' + str(fun_index) + ' of ' + str(
                        len(fun_bdds_roots)) + '. SubBDD Root:' + str(fun_root.var) + '.'
                    pbi_fun_subbdd_root = bdd_manager.apply('or', current_root, fun_root)
                else:
                    log_str = 'APPLY AND. PBI ' + str(pbi_index) + '. SubBDD ' + str(fun_index) + ' of ' + str(
                        len(fun_bdds_roots)) + '. SubBDD Root:' + str(fun_root.var) + '.'
                    pbi_fun_subbdd_root = bdd_manager.apply('and', current_root, fun_root)
                bdd_manager.collect_garbage()
                print(log_str, 'Size of current BDD after apply:', pbi_fun_subbdd_root.dag_size)
                current_root = pbi_fun_subbdd_root
                if current_root.dag_size > bdd_max_size:
                    bdd_max_size = current_root.dag_size
                if current_root.dag_size == 1:
                    unsat_flag = True
                    print('BDD has collapsed into one vertex, while applying interval', pbi_index, 'to subbdds.')
                    print('Vertex:', bdd_manager.to_expr(current_root))
                    indices_unsat.append(fun_index + 1)
                    break
            final_roots.append(current_root)
            bdd_max_sizes.append(bdd_max_size)
            times_for_intervals.append(time.time() - pbi_start_time)
            if not unsat_flag:
                print('Assignments for current root', pbi_index, end=':\n')
                for index_assign, d in enumerate(bdd_manager.pick_iter(current_root)):
                    print(index_assign, d)
                    if index_assign >= 100:
                        print('and others...')
                        break
    else:
        pass
        # TODO сделать без интервалов
    print()
    print('Final. Separated BDD construction with PBI is complete.')
    print('Final. Number of PBI:', nof_intervals)
    print('Final. PBI BDDs sizes:', pbi_bdds_sizes)
    print('Final. PBI BDDs maximum sizes during construction:', pbi_bdds_max_sizes)
    print('Final. Initial number of BDDs:', len(fun_bdds_roots))
    print('Final. Function subbdds sizes:', fun_bdds_sizes)
    print('Final. Function subbdds maximum sizes during construction:', fun_bdds_max_sizes)
    print('Final. Max sizes by intervals:', bdd_max_sizes)
    print('Final. Absolute max size:', max(bdd_max_sizes))
    print('Final. Funbdds indices causing graph elimination:', indices_unsat)
    print('Final. Times for check intervals:', [round(x, 2) for x in times_for_intervals])
    print('Final. Total time for applying:', round(sum(times_for_intervals), 2))


def Problems2BDD_dd_format(sortedproblems: list, bdd_manager, problem_type='DNF'):
    roots = []
    max_sizes = []
    for index, problem in enumerate(sortedproblems):
        # print('\nStart construction of subbdd', index)
        root, max_size = Problem2BDD_dd_format(problem, bdd_manager, problem_type)
        roots.append(root)
        max_sizes.append(max_size)
    return roots, max_sizes


# Подразумевается, что исходная формула всегда КНФ. Если мы строим диаграмму по её отрицанию,
# то в поле problem_type передаём 'DNF', иначе 'CNF'.
def Problem2BDD_dd_format(sortedproblem: list, bdd_manager, problem_type='DNF'):
    first_clause = sortedproblem.pop()
    current_problem_root = Clause2BDD_dd_format(first_clause, bdd_manager, problem_type)
    max_size = current_problem_root.dag_size
    # print('Clause:', first_clause)
    # print('Current root expr:', current_problem_root.to_expr())
    for clause in sortedproblem:
        # print('Clause:', clause)
        current_clause_root = Clause2BDD_dd_format(clause, bdd_manager, problem_type)
        if problem_type == 'DNF':
            current_problem_root = bdd_manager.apply('or', current_problem_root, current_clause_root)
        else:
            current_problem_root = bdd_manager.apply('and', current_problem_root, current_clause_root)
        # print('Current root expr:', current_problem_root.to_expr())
        if current_problem_root.dag_size > max_size:
            max_size = current_problem_root.dag_size
    bdd_manager.collect_garbage()
    return current_problem_root, max_size


def Clause2BDD_dd_format(clause, bdd_manager, problem_type='DNF'):
    literals = ['!x'+str(abs(x)) if x < 0 else 'x'+str(abs(x)) for x in clause]
    if problem_type == 'DNF':
        expr_str = r' /\ '.join(literals)
    else:
        expr_str = r' \/ '.join(literals)
    # print('Expr:', expr_str)
    root = bdd_manager.add_expr(expr_str)
    return root


def DJDstoBDDs(djds, numproc):
    try:
        # переводим каждую поддиаграмму в бдд
        subdjd_to_bdd_times = []
        bdds = []
        if numproc == 1:
            for djd_diagram in djds:
                new_bdd_diagram, transform_time = DJDtoBDD(djd_diagram)
                new_bdd_diagram.EnumerateBDDiagramNodes()
                subdjd_to_bdd_times.append(transform_time)
                bdds.append(new_bdd_diagram)
        else:
            with multiprocessing.Pool(min(numproc, len(djds))) as p:
                for result in p.map(DJDtoBDD, djds):
                    new_bdd_diagram = result[0]
                    transform_time = result[1]
                    subdjd_to_bdd_times.append(transform_time)
                    bdds.append(new_bdd_diagram)
        return bdds, subdjd_to_bdd_times
    except Exception as ex:
        print('ERROR DJDstoBDDs', ex)
        raise ex


def PrintFinalStats(diagram):
    print()
    print('Final. Total number of removed nonbinary links: ' + str(diagram.removed_nonbinaries_total))
    print('Final. Total number of actions with links: ' + str(diagram.actions_with_links_))
    print('Final. Max size of diagram: ' + str(diagram.max_size))
    print('Final. Final size of diagram: ' + str(diagram.VertexCount()))
    print('Final. Number of created nodes: ' + str(diagram.new_nodes_))
    print('Final. Number of deleted nodes: ' + str(diagram.deleted_nodes_))


def make_pairs(diagrams):
    for i in range(0, len(diagrams), 2):
        yield tuple(diagrams[i:i + 2])


def ConjoinBDDs(diagrams_pair):
    try:
        conjoin_start_time = time.time()
        diagram1 = diagrams_pair[0]
        diagram2 = diagrams_pair[1]
        log_lines = ['\n',
                     '---------------------------------------------------------------------------------------------',
                     'Current. Start conjoin two diagrams.']
        # print('\n')
        # print('---------------------------------------------------------------------------------------------')
        # print('Start conjoin two diagrams.')
        # соединяем две диаграммы в одну, чтобы потом избавляться от небинарностей
        sorted_nodes2 = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram2.order_, diagram2.table_.values())
        max_vertex = len(diagram1.table_)
        current_vertex_id = max_vertex + 1
        log_lines.append('\nCurrent. Size of diagram 1: ' + str(diagram1.VertexCount()))
        log_lines.append('Current. Size of diagram 2: ' + str(diagram2.VertexCount()))
        # print('\nSize of diagram 1:', diagram1.VertexCount())
        # print('Size of diagram 2:', diagram2.VertexCount())
        # diagram1.PrintCurrentTable('Table 1:')
        # diagram2.PrintCurrentTable('Table 2:')
        for node in sorted_nodes2:
            node.vertex_id = current_vertex_id
            current_vertex_id += 1
        if type(diagram1) != DisjunctiveDiagram and type(diagram2) != DisjunctiveDiagram:
            diagram1.new_nodes_ += diagram2.new_nodes_
            diagram1.deleted_nodes_ += diagram2.deleted_nodes_
            diagram1.actions_with_links_ += diagram2.actions_with_links_
            diagram1.max_size = max(diagram1.max_size, diagram2.max_size)
            diagram1.removed_nonbinaries_total += diagram2.removed_nonbinaries_total
        DisjunctiveDiagramsBuilder.GluingNodes(sorted_nodes2, diagram1)
        # EnumerateBDDiagramNodes(diagram1)
        # print('\n\nDiagram before remove nonbinary:', diagram1)
        del diagram2
        diagram1.roots_ = diagram1.GetRoots()
        new_diagram, transform_time_ = DJDtoBDD(diagram1)
        # print('\nDiagram after remove nonbinary:', new_diagram)
        log_lines.append('Current. Size of result diagram: ' + str(new_diagram.VertexCount()))
        # print('Size of result diagram:', new_diagram.VertexCount())
        # new_diagram.PrintCurrentTable('New table:')
        log_lines.append('\nCurrent. Total number of actions with links to construct new diagram: ' +
                         str(new_diagram.actions_with_links_))
        log_lines.append('Current. Number of vertices in a result diagram: ' + str(new_diagram.VertexCount()))
        log_lines.append('Current. Number of links in a result diagram: ' + str(new_diagram.LinksCount()) + '\n')
        # print('\n Total number of actions with links to construct new diagram:', new_diagram.actions_with_links_)
        # print(' Number of vertices in a result diagram:', new_diagram.VertexCount())
        # print(' Number of links in a result diagram:', new_diagram.LinksCount(), '\n')
        if len(new_diagram.table_sizes) < 1000:
            log_lines.append('Current. Changes of number of vertices in diagram: ' +
                             ' '.join([str(x) for x in new_diagram.table_sizes]))
            # print('Changes of number of vertices in diagram:', new_diagram.table_sizes)
        if len(new_diagram.table_sizes) > 1:
            log_lines.append('Current. Number of removed nonbinary links: ' +
                             str(new_diagram.removed_nonbinaries_current))
            log_lines.append('Current. Initial size of diagram: ' + str(new_diagram.table_sizes[0]))
            log_lines.append('Current. Final size of diagram: ' + str(new_diagram.VertexCount()))
            log_lines.append('Current. Max size of diagram: ' + str(new_diagram.max_size))
            log_lines.append('Current. Min size of diagram: ' + str(min(new_diagram.table_sizes)))
            log_lines.append('Current. Avg size of diagram: ' + str(mean(new_diagram.table_sizes)))
            log_lines.append('Current. Median size of diagram: ' + str(median(new_diagram.table_sizes)))
            log_lines.append('Current. Sd of size of diagram: ' +
                             str(round(math.sqrt(variance(new_diagram.table_sizes)), 2)))
            # print('Number of removed nonbinary links:', len(new_diagram.table_sizes) - 1)
            # print('Initial size of diagram:', new_diagram.table_sizes[0])
            # print('Final size of diagram:', new_diagram.table_sizes[-1])
            # print('Max size of diagram:', max(new_diagram.table_sizes))
            # print('Min size of diagram:', min(new_diagram.table_sizes))
            # print('Avg size of diagram:', mean(new_diagram.table_sizes))
            # print('Median size of diagram:', median(new_diagram.table_sizes))
            # print('Sd of size of diagram:', round(math.sqrt(variance(new_diagram.table_sizes)), 2))
        conjoin_time = time.time() - conjoin_start_time
        return new_diagram, conjoin_time, log_lines
    except Exception as ex:
        print('ERROR ConjoinBDDs', ex)
        raise ex


def DJDtoBDD(djddiagram):
    try:
        start_transform_time = time.time()
        bdd_diagram = BDDiagram(djddiagram)
        transform_time = time.time() - start_transform_time
        return [bdd_diagram, transform_time]
    except Exception as ex:
        print('ERROR DJDtoBDD', ex)
        raise ex


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
            self.actions_with_links_ = 0
            self.max_size = diagram.VertexCount()
            self.removed_nonbinaries_total = 0
        else:
            self.new_nodes_ = diagram.new_nodes_
            self.deleted_nodes_ = diagram.deleted_nodes_
            self.actions_with_links_ = diagram.actions_with_links_
            self.max_size = diagram.max_size
            self.removed_nonbinaries_total = diagram.removed_nonbinaries_total
        self.removed_nonbinaries_current = 0
        self.table_sizes = []
        self.nonbinary_queue = []
        self.changed_hash_nodes = set()
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

    def PrintCurrentTableWithKey(self, preambule=''):
        print('\n', preambule)
        if len(self.table_) > 0:
            for key, node in self.table_.items():
                node.PrintNode('  key ' + str(key))
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
            # json_string = json.dumps(table_dict)
            with open(filename, 'w') as outfile:
                json.dump(table_dict, outfile, indent=2)
        else:
            print('Cannot dump diagram to json-file, because table is empty.')

    def DumpTableJSON_ddformat_manually(self, filename):
        assert len(self.table_) > 0, 'Cannot dump diagram to json-file, because table is empty.'
        sorted_nodes = DisjunctiveDiagramsBuilder.LitLessSortNodes(self.order_, self.table_.values())
        rev_order = list(reversed(self.order_))
        for node in sorted_nodes:
            node.level = rev_order.index(node.Value())
        sorted_vars_with_levels = sorted([('x' + str(node.Value()), node.level) for node in sorted_nodes if
                                          node.IsNotTerminal()], key=lambda x: x[1])
        negated_nodes = set()
        with open(filename, 'w') as f:
            print('{', file=f)
            print('\"level_of_var\": {', end='', file=f)
            for index, pair in enumerate(sorted_vars_with_levels):
                if index < len(sorted_vars_with_levels)-1:
                    print('\"'+pair[0]+'\": ', pair[1], sep='', end=', ', file=f)
                else:
                    print('\"' + pair[0] + '\": ', pair[1], sep='', end='},\n', file=f)
            for index, node in enumerate(sorted_nodes):
                if node.IsNotTerminal():
                    negated_node = False
                    if node.FirstLowChild().IsTrueLeaf():
                        low = "T"
                    elif node.FirstLowChild().IsQuestionLeaf():
                        low = "F"
                    else:
                        if node.FirstLowChild().vertex_id in negated_nodes:
                            low = -node.FirstLowChild().vertex_id
                        else:
                            low = node.FirstLowChild().vertex_id
                    if node.FirstHighChild().IsTrueLeaf():
                        high = "T"
                    elif node.FirstHighChild().IsQuestionLeaf():
                        negated_node = True
                        negated_nodes.add(node.vertex_id)
                        high = "F"
                    else:
                        if node.FirstHighChild().vertex_id in negated_nodes:
                            negated_node = True
                            high = -node.FirstHighChild().vertex_id
                        else:
                            high = node.FirstHighChild().vertex_id
                    if negated_node:
                        if low == "T":
                            low = "F"
                        elif low == "F":
                            low = "T"
                        else:
                            low = -low
                        if high == "T":
                            high = "F"
                        elif high == "F":
                            high = "T"
                        else:
                            high = -high
                    if index < len(sorted_nodes)-1:
                        # print('\"' + str(node.vertex_id) + '\": ', [node.level, low, high], ',', sep='', file=f)
                        print('\"' + str(node.vertex_id) + '\":', sep='', end=' ', file=f)
                        print('[', node.level, sep='', end=', ', file=f)
                        print('\"'+low+'\"' if type(low) == str else low, sep='', end=', ', file=f)
                        print('\"'+high+'\"' if type(high) == str else high, sep='', end='],\n', file=f)
                    else:
                        # print('\"' + str(node.vertex_id) + '\": ', [node.level, low, high], ',', sep='', file=f)
                        print('\"' + str(node.vertex_id) + '\":', sep='', end=' ', file=f)
                        print('[', node.level, sep='', end=', ', file=f)
                        print('\"'+low+'\"' if type(low) == str else low, sep='', end=', ', file=f)
                        print('\"'+high+'\"' if type(high) == str else high, sep='', end=']\n', file=f)
            print('\"roots\": ', [self.main_root_.vertex_id if self.main_root_.vertex_id not in negated_nodes else -self.main_root_.vertex_id], ',', sep='', file=f)
            print('}', file=f)

    def DumpTableJSON_ddformat(self, filename):
        assert len(self.table_) > 0, 'Cannot dump diagram to json-file, because table is empty.'
        sorted_nodes = DisjunctiveDiagramsBuilder.LitLessSortNodes(self.order_, self.table_.values())
        rev_order = list(reversed(self.order_))
        for node in sorted_nodes:
            node.level = rev_order.index(node.Value())
        sorted_vars_with_levels = sorted([("x" + str(node.Value()), node.level) for node in sorted_nodes if
                                          node.IsNotTerminal()], key=lambda x: x[1])
        negated_nodes = set()
        root = self.main_root_.vertex_id
        bdd_dict = dict()
        bdd_dict["level_of_var"] = dict()
        for pair in sorted_vars_with_levels:
            bdd_dict["level_of_var"][pair[0]] = pair[1]
        for node in sorted_nodes:
            negated_node = False
            if node.IsNotTerminal():
                if node.FirstLowChild().IsTrueLeaf():
                    low = "T"
                elif node.FirstLowChild().IsQuestionLeaf():
                    low = "F"
                else:
                    if node.FirstLowChild().vertex_id in negated_nodes:
                        low = -node.FirstLowChild().vertex_id
                    else:
                        low = node.FirstLowChild().vertex_id
                if node.FirstHighChild().IsTrueLeaf():
                    high = "T"
                elif node.FirstHighChild().IsQuestionLeaf():
                    negated_node = True
                    negated_nodes.add(node.vertex_id)
                    high = "F"
                else:
                    if node.FirstHighChild().vertex_id in negated_nodes:
                        negated_node = True
                        negated_nodes.add(node.vertex_id)
                        high = -node.FirstHighChild().vertex_id
                    else:
                        high = node.FirstHighChild().vertex_id
                # print('\nBefore negated', node.vertex_id, [node.level, low, high])
                if negated_node:
                    if low == "T":
                        low = "F"
                    elif low == "F":
                        low = "T"
                    else:
                        low = -low
                    if high == "T":
                        high = "F"
                    elif high == "F":
                        high = "T"
                    else:
                        high = -high
                bdd_dict[str(node.vertex_id)] = [node.level, low, high]
                # print('Negated flag', negated_node)
                # print('Negated nodes', negated_nodes)
                # print('After negated', node.vertex_id, [node.level, low, high])
        bdd_dict["roots"] = [root] if root not in negated_nodes else [-root]
        outfile_lines = '{\n'
        outfile_lines += '"level_of_var": ' + json.dumps(bdd_dict["level_of_var"]) + ',\n'
        outfile_lines += '"roots": ' + json.dumps(bdd_dict["roots"])
        for key in bdd_dict.keys():
            if key != 'roots' and key != 'level_of_var':
                node_str = '"{k}": '.format(k=key) + json.dumps(bdd_dict[key])
                outfile_lines += ',\n' + node_str
        outfile_lines += '\n}'
        # pprint.pprint(bdd_dict)
        # bdd_dict_json_str = json.dumps(bdd_dict)
        with open(filename, 'w') as f:
            print(outfile_lines, file=f)
        # json.dump(bdd_dict, open(filename, 'w'))

    # Получаем КНФ из диаграммы (все пути из корней в терминальную 'true')
    def GetCNFFromBDD(self):
        cnf = []
        node_paths = []
        true_leaf = self.GetTrueLeaf()
        for node in true_leaf.high_parents:
            clause = [node.var_id]
            node_path = [node]
            WritePaths(cnf, node_paths, node_path, clause)
        for node in true_leaf.low_parents:
            clause = [-node.var_id]
            node_path = [node]
            WritePaths(cnf, node_paths, node_path, clause)
        NegateProblem(cnf)
        return cnf, node_paths

    # Получаем КНФ из диаграммы (все пути из корней в терминальную 'true')
    def GetPathsToTrue(self):
        cnf = []
        node_paths = []
        true_leaf = self.GetTrueLeaf()
        for node in true_leaf.high_parents:
            clause = [node.var_id]
            node_path = [node]
            WritePaths(cnf, node_paths, node_path, clause)
        for node in true_leaf.low_parents:
            clause = [-node.var_id]
            node_path = [node]
            WritePaths(cnf, node_paths, node_path, clause)
        return cnf, node_paths

    # Получаем выполняющие наборы из диаграммы (все пути из корней в терминальную 'question')
    def GetSatAssignmentFromDiagram(self):
        cnf = []
        node_paths = []
        question_leaf = self.GetQuestionLeaf()
        for node in question_leaf.high_parents:
            clause = [node.var_id]
            node_path = [node]
            WritePaths(cnf, node_paths, node_path, clause)
        for node in question_leaf.low_parents:
            clause = [-node.var_id]
            node_path = [node]
            WritePaths(cnf, node_paths, node_path, clause)
        return cnf, node_paths

    def EnumerateBDDiagramNodes(self):
        vertex_id = 0
        for node in sorted(self.table_.values(), key=lambda x: self.order_.index(x.Value())):
            node.vertex_id = vertex_id
            vertex_id += 1

    # Возвращает размер диаграммы в байтах
    def DiagramSize(self):
        return len(self.table_)

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
    for i in range(len(sorted_roots_) - 1):
        # print('Connect root', str(sorted_roots_[i].vertex_id) + '_' + str(sorted_roots_[i].var_id),
        #       ' to root', str(sorted_roots_[i+1].vertex_id) + '_' + str(sorted_roots_[i+1].var_id))
        # присоединяем нижний корень к верхнему по двум полярностям
        ConnectRoots(sorted_roots_[i + 1], sorted_roots_[i], diagram)
    # теперь diagram.roots_ неправильная, потому что хэши поменялись (бтв, в table всё обновлено), но это и неважно
    # print('Roots', [(x.vertex_id, x.var_id, x.node_type) for x in diagram.roots_])
    diagram.main_root_ = main_root
    diagram.table_sizes.append((diagram.VertexCount()))
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
        # print('Current size of diagram:', diagram.VertexCount())
        # print('Current number of actions with links', diagram.actions_with_links_)
        sorted_nodes = DisjunctiveDiagramsBuilder.LitLessSortNodeswrtOrderAndVertex(diagram.order_,
                                                                                    diagram.table_.values())
        # print('Current number of nodes', len(sorted_nodes))
        # print('Current number of deleted nodes', diagram.deleted_nodes_)
        first_nonbinary_node, polarity = FindFirstNonbinaryNode(sorted_nodes)
        # print('First nonbinary node', first_nonbinary_node.vertex_id, 'var', first_nonbinary_node.var_id)
        # first_nonbinary_node.PrintNode('First nonbinary node:')
        if polarity == 'both':
            diagram.nonbinary_queue.append([first_nonbinary_node, 1])
            diagram.nonbinary_queue.append([first_nonbinary_node, 0])
        # BDDiagram.nonbinary_queue.put([first_nonbinary_node, polarity])
        else:
            diagram.nonbinary_queue.append([first_nonbinary_node, polarity])
        # while not BDDiagram.nonbinary_queue.empty():
        while diagram.nonbinary_queue:
            # print('\nCurrent size of queue', len(diagram.nonbinary_queue))
            # diagram.PrintCurrentTable('\n-----------------------------------\nCurrent table:')
            host = diagram.nonbinary_queue.pop()
            # host[0].PrintNode('Current host:')
            # print('Polarity:', host[1])
            # BDDiagram.PrintCurrentQueue(diagram)
            RemoveNonbinaryLink(host[0], host[1], diagram)
    # diagram.PrintCurrentTable('Table after BDD transformation:')
    # print('\nEnd size of queue (should be 0)', len(diagram.nonbinary_queue))


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
        if diagram.max_size < diagram.VertexCount():
            diagram.max_size = diagram.VertexCount()
        diagram.removed_nonbinaries_current += 1
        diagram.removed_nonbinaries_total += 1
        diagram.table_sizes.append((diagram.VertexCount()))
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
    ConnectNodesDouble(None, None, lower, upper, diagram)


def ConnectNodesDouble(host, polarity, lower, upper, diagram):
    # diagram.PrintCurrentTable('ConnectNodesDouble 0 table:')
    # проверяем количество родителей у узла, в которому приклеиваем
    # если больше 1, то нужно будет его расклеивать
    # когда склеиваем корни такой ситуации вообще не должно происходить
    # print('')
    # if host is not None:
    #     host.PrintNode('Current host:')
    #     host.HashKey()
    #     host.PrintNode('Current host 2:')
    # lower.PrintNode('Current lower:')
    # upper.PrintNode('Current upper:')
    old_upper = upper
    upper = CheckNodeForUngluing(diagram, upper, host, polarity)
    # if old_upper is not upper:
    # upper.PrintNode('New upper:')

    # diagram.PrintCurrentTable('ConnectNodesDouble 1 table:')

    # удаляем из таблицы всё от upper (включительно) наверх
    diagram.changed_hash_nodes.clear()
    if host is not None:
        if old_upper is upper:
            DeletingNodesFromTable(upper, diagram, False)
        else:
            DeletingNodesFromTable(upper, diagram, True)
    else:
        DeletingNodesFromTable(lower, diagram, False)
        DeletingNodesFromTable(upper, diagram, False)
        # del diagram.table_[upper.hash_key]
        # del diagram.table_[lower.hash_key]

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
    # for node in diagram.changed_hash_nodes:
    #     node.PrintNode('  Changed hash node:')
    if host is not None:
        # print('1st')
        host, upper = GluingNodes(upper, host, diagram)
    elif upper is not upper_del:
        # print('2nd')
        # lower.HashKey()
        # diagram.table_[lower.hash_key] = lower
        GluingNodes(None, None, diagram)
        upper.HashKey()
        diagram.table_[upper.hash_key] = upper
    else:
        GluingNodes(None, None, diagram)

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

    # if type(host) == DiagramNode:
    #     host.PrintNode('After changes host:')
    #     host.HashKey()
    #     host.PrintNode('After changes host 2:')
    # else:
    #     print('After changes host:', host)
    # if type(lower) == DiagramNode:
    #     lower.PrintNode('After changes lower:')
    # else:
    #     print('After changes lower:', lower)
    # if type(upper) == DiagramNode:
    #     upper.PrintNode('After changes upper:')
    # else:
    #     print('After changes upper:', upper)

    return [host, upper, upper_nonbinary_polarity]


def RemoveLinkFromHostToLower(diagram, host, lower, polarity):
    # print('RemoveLinkFromHostToLower before Host:', end=' ')
    # host.PrintNode()
    # print('RemoveLinkFromHostToLower before Lower:', end=' ')
    # lower.PrintNode()
    if polarity == 1:
        # host_len_childs_before = len(host.high_childs)
        # lower_len_parents_before = len(lower.high_parents)
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
                lower.PrintNode(' ERROR lower')
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
                # print('Upper have more than 1 parent. Need ungluing.')
                diagram.new_nodes_ += 1
                # тут нам надо расклеить узел на два так, чтобы у одного были все родители, кроме host
                # а у второго только host
                if host is None:
                    print('ERROR host is None, but try to ungluing')
                    raise Exception('ERROR host is None, but try to ungluing')
                # print('Old upper')
                # upper.PrintNode()
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
    # print('\nCheckNonbinaryWithTrueNode')
    # node.PrintNodeWithoutParents()
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
    # print('\nCheckNonbinaryWithQuestionNode')
    # node.PrintNodeWithoutParents()
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
            DeleteNodeWithoutParents(child, diagram)
        diagram.actions_with_links_ += 1
        node.high_childs = [diagram.GetTrueLeaf()]
        diagram.GetTrueLeaf().high_parents.append(node)
    elif polarity == 0:
        for child in node.low_childs:
            diagram.actions_with_links_ += 1
            child.low_parents = [x for x in child.low_parents if x is not node]
            DeleteNodeWithoutParents(child, diagram)
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
        # print('High childs:')
        for high_child in node.high_childs:
            # print('High child before:', end=' ')
            # high_child.PrintNode()
            diagram.actions_with_links_ += 1
            high_child.high_parents = [x for x in high_child.high_parents if x is not node]
            DeleteNodeWithoutParents(high_child, diagram)
            # print('High child after:', end=' ')
            # high_child.PrintNode()
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
        # node.PrintNode('Double True child deleting node:')
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
                print('ERROR node is node_to_which_glue')
                raise Exception('ERROR node is node_to_which_glue')
            # node.PrintNode(' Glued node')
            # node_to_which_glue.PrintNode('    with node')
            # node_to_which_glue.HashKey()
            # node_to_which_glue.PrintNode('    with node 2')
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


def ReplaceParentsLinksToNode(node, node_to_which_glue, diagram):
    for parent in node.high_parents:
        diagram.actions_with_links_ += 1
        parent.high_childs = [x for x in parent.high_childs if x is not node and x is not node_to_which_glue]
        parent.high_childs.append(node_to_which_glue)
        for tmpnode in node_to_which_glue.high_parents:
            if tmpnode is parent:
                break
        else:
            # print('add as highparent ', (parent.Value(), parent), 'to node', (it_node.Value(), it_node))
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
            # print('add as lowparent ', (parent.Value(), parent), 'to node', (it_node.Value(), it_node))


def DeleteChildsLinksToNode(node, diagram):
    diagram.actions_with_links_ += len(node.high_childs) + len(node.low_childs)
    for child in node.high_childs:
        child.high_parents = [x for x in child.high_parents if x is not node]
    for child in node.low_childs:
        child.low_parents = [x for x in child.low_parents if x is not node]


# Рекурсивное удаление узлов из таблицы от node наверх
def DeletingNodesFromTable(node, diagram, copy_flag):
    diagram.changed_hash_nodes.add(node)
    if ((node.hash_key in diagram.table_) or copy_flag) and \
            node is not diagram.GetTrueLeaf() and \
            node is not diagram.GetQuestionLeaf():
        if diagram.table_[node.hash_key] is node:
            # node.PrintNode('Delete from table:')
            del diagram.table_[node.hash_key]
        # else:
        # node.PrintNode('no Delete from table node:')
        # diagram.table_[node.hash_key].PrintNode('no Delete from table diagram.table_[node.hash_key]:')
        for parent in set(node.high_parents + node.low_parents):
            # parent.PrintNode('Delete from table parent:')
            DeletingNodesFromTable(parent, diagram, False)
    # else:
    #     print(1 if node.hash_key in diagram.table_ else 0)
    #     node.PrintNode('   node now')
    #     print(node.HashKey_test_())
    #     diagram.PrintCurrentTableWithKey('    table now')
    #     print(1 if node is not diagram.GetTrueLeaf() else 0)
    #     print(1 if node is not diagram.GetQuestionLeaf() else 0)


def CleaningDiagram(diagram):
    sorted_nodes = DisjunctiveDiagramsBuilder.LitLessSortNodeswrtOrderAndVertex(diagram.order_, diagram.table_.values())
    for node in sorted_nodes:
        # print(node.Value())
        if len(node.low_childs) > 0 and len(node.high_childs) > 0:
            if node.low_childs[0] is node.high_childs[0]:
                diagram.changed_hash_nodes.clear()
                # print('Diagram:', diagram)
                # diagram.PrintCurrentTable('Table before deletion of useless node')
                DeletingNodesFromTable(node, diagram, False)
                # node.PrintNode('  Delete useless node:')
                DeleteUselessNode(node, diagram)
                GluingNodes(None, None, diagram)
                # diagram.PrintCurrentTable('Table after deletion of useless node')


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

    # удаляем связи детей с узлом
    child = node.high_childs[0]
    child.high_parents = [x for x in child.high_parents if x is not node]
    child.low_parents = [x for x in child.low_parents if x is not node]
    if node.node_type == DiagramNodeType.RootNode:
        DeletingNodesFromTable(child, diagram, False)
        child.node_type = DiagramNodeType.RootNode
        child.HashKey()
        diagram.table_[child.hash_key] = child
    else:
        # переносим связь вершины с 1-потомком 1-родителю (у родителя точно 1 потомок по 1-связи, а вот у
        # потомка может быть больше 1 родителя, если это терминальная вершина)
        for hp in node.high_parents:
            # node.high_parents[0].PrintNode('   high parent before')
            # node.high_childs[0].PrintNode('   high child before')
            hp.high_childs[0] = node.high_childs[0]
            node.high_childs[0].high_parents.append(hp)
            # node.high_parents[0].PrintNode('   high parent after')
            # node.high_childs[0].PrintNode('   high child after')

        # переносим связь вершины с 0-потомком 0-родителю
        for lp in node.low_parents:
            # node.low_parents[0].PrintNode('   low parent before')
            # node.low_childs[0].PrintNode('   low child before')
            lp.low_childs[0] = node.low_childs[0]
            node.low_childs[0].low_parents.append(lp)
            # node.low_parents[0].PrintNode('   low parent after')
            # node.low_childs[0].PrintNode('   low child after')

    del node


def WritePaths(problem, node_paths, node_path, clause):
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


# переводим через файл мои диаграммы в формат пакета dd, задавая порядок
def mybdds2ddbdds(mybdds, bdd_manager, negate_flag, preambule):
    dd_bdds = []
    for index, bdd in enumerate(mybdds):
        curr_preambule = preambule + str(index)
        root = mybdd2ddbdd(bdd, bdd_manager, negate_flag, curr_preambule)
        dd_bdds.append(root)
    return dd_bdds


# переводим через файл мою диаграмму в формат пакета dd, задавая порядок
def mybdd2ddbdd(mybdd: BDDiagram, bdd_manager, negate_flag, preambule=''):
    assert type(mybdd) == BDDiagram, 'ERROR mybdd2ddbdd. Expect BDDiagram, got ' + str(type(mybdd))
    filename = preambule + '_tmp.json'
    mybdd.DumpTableJSON_ddformat(filename)
    root = bdd_manager.load(filename)[0]
    if negate_flag:
        root = bdd_manager.add_expr(r'!{u}'.format(u=root))
    bdd_manager.collect_garbage()
    # os.remove(filename)
    # bdd_manager.dump('./tmp_/_' + filename, roots=[root])
    # bdd_manager.dump('./tmp_/_' + filename+'.pdf')
    return root


def create_and_expr(vars):
    pass
