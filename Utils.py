from Types import *
from DimacsParser import *


def ReadProblem(options):
    lines = open(options.path, 'r').readlines()
    problem, order, comments, var_count, lit_count, min_var_num, max_var_num, layers = DimacsParser(lines)
    print('Lit count:'.ljust(30, ' '), lit_count)
    print('Variables:'.ljust(30, ' '), var_count)
    print('Lowest variable number:'.ljust(30, ' '), min_var_num)
    print('Highest variable number:'.ljust(30, ' '), max_var_num)
    if options.order_type == 'activity':
        print('Order:'.ljust(30, ' '), 'activity')
        if order is None:
            raise RuntimeError('No activity order in DIMACS file')
    elif options.order_type == 'frequency':
        print('Order:'.ljust(30, ' '), 'frequency')
        order = FrequencyOrder(problem, min_var_num, max_var_num)
    elif options.order_type == 'revfrequency':
        print('Order:'.ljust(30, ' '), 'reversed frequency')
        order = ReversedFrequencyOrder(problem, min_var_num, max_var_num)
    elif options.order_type == 'direct':
        print('Order:'.ljust(30, ' '), 'direct')
        if max_var_num != 0:
            order = [x for x in reversed(range(1, max_var_num+1))]
        else:
            raise RuntimeError('No maximum variable found, check DIMACS file.')
    elif options.order_type == 'layers':
        order = LayersDirectOrder(layers, min_var_num, max_var_num)
    order.insert(0, 'true')
    order.insert(0, '?')
    return var_count, problem, order, comments


def FrequencyOrder(problem, min_var_num, max_var_num):
    if min_var_num != 0 and max_var_num != 0:
        counter = [0 for x in range(max_var_num+1)]
        for clause in problem:
            for lit in clause:
                counter[abs(lit)] += 1
        counter = list(enumerate(counter))
        counter.sort(key=lambda x: x[1])
        order = [x[0] for x in counter if x[1] > 0]
        return order
    else:
        raise RuntimeError('No minimum and maximum variables found, check DIMACS file.')


def ReversedFrequencyOrder(problem, min_var_num, max_var_num):
    if min_var_num != 0 and max_var_num != 0:
        counter = [0 for x in range(max_var_num+1)]
        for clause in problem:
            for lit in clause:
                counter[abs(lit)] += 1
        counter = list(enumerate(counter))
        counter.sort(key=lambda x: x[1])
        counter.reverse()
        order = [x[0] for x in counter if x[1] > 0]
        return order
    else:
        raise RuntimeError('No minimum and maximum variables found, check DIMACS file.')


def LayersDirectOrder(layers, min_var_num, max_var_num):
    if min_var_num != 0 and max_var_num != 0:
        # print('Layers:', layers)
        for i in range(len(layers)):
            layers[i].sort(key=lambda x: abs(x))
        # print('Sorted layers:', layers)
        order = list(reversed(flatten(layers)))
        return order
    else:
        raise RuntimeError('No minimum and maximum variables found, check DIMACS file.')


def flatten(l):
    return [item for sublist in l for item in sublist]


def ExtractVarSet(problem, var_set):
    pass


def ExtractVarCounterMap(problem, var_map):
    pass


# Минимальный и максимальный номер переменной
def GetMinMaxVars(problem, min_var_id, max_var_id):
    pass


# Разделить путь к папке и имя файла
def SplitFilename(path):
    if '\\' not in path:
        dir = ''.join(path.split('/')[:-1])
        filename = ''.join(path.split('/')[-1])
    else:
        dir = ''.join(path.split('\\')[:-1])
        filename = ''.join(path.split('\\')[-1])
    return dir, filename


# Разделить имя файла на имя и суффикс
def SplitFileSuffix(filename):
    name = ''.join(filename.split('.')[:-1])
    suffix = ''.join(filename.split('.')[-1])
    return name, suffix


# Проверяем существование файла
def FileExists(options):
    return os.path.isfile(options.path)


# Число литералов в формуле
def GetLiteralCount(problem):
    pass


# Размер формулы в памяти
def GetProblemBinarySize(problem):
    pass


# Размер выделенной памяти под формулу
def GetProblemMemoryAlloc(problem):
    pass


def FillVarOrder(problem, order, order_type):
    pass


def GetProblemType(str_type):
    if str_type == 'cnf':
        ptype = ProblemType.Cnf
    elif str_type == 'dnf':
        ptype = ProblemType.Dnf
    elif str_type == 'conflict':
        ptype = ProblemType.Conflict
    else:
        raise RuntimeError('Unknown type of problem')
    return ptype


def WritePathsToFile(paths, filename):
    with open(filename, 'w') as f:
        for path in paths:
            print(*path, sep=' ', file=f)


# Отрицание формулы. Применяется для перехода от КНФ конфликтных баз к ДНФ.
def NegateProblem(problem):
    negate_problem = copy.deepcopy(problem)
    for i in range(len(negate_problem)):
        for j in range(len(negate_problem[i])):
            negate_problem[i][j] *= -1
    return negate_problem


def DivideProblem(problem, order):
    nof_vars = get_max_var(problem)
    problems = [[] for x in range(nof_vars)]
    for clause in problem:
        clause = sorted(clause, key=lambda x: order.index(abs(x)), reverse=True)
        problems[abs(clause[0])-1].append(clause)
    problems = [x for x in problems if len(x) > 0]
    return problems


def GetInputs(problem_comments, nof_intervals):
    if nof_intervals > 0:
        for comment in problem_comments:
            if 'c inputs' in comment:
                inputs = list(map(int, comment.split(':')[1].split()))
                break
        else:
            print('Comments:', *problem_comments, sep='\n')
            raise Exception('There is no inputs list in a comments.')
        return inputs
    else:
        return None


def get_max_var(problem):
    max_var = 0
    for clause in problem:
        for lit in clause:
            if abs(lit) > max_var:
                max_var = abs(lit)
    return max_var


def SortProblems(problems, order):
    for i in range(len(problems)):
        problems[i] = SortProblem(problems[i], order)
    problems.sort(key=lambda x: order.index(abs(x[0][0])), reverse=True)
    return problems


def SortProblem(problem, order):
    for i in range(len(problem)):
        problem[i] = sorted(problem[i], key=lambda x: order.index(abs(x)), reverse=True)
    problem.sort(key=lambda x: len(x))
    return problem


def CreateLogDir(options):
    current_dir = os.getcwd()
    logs_dir = os.path.join(current_dir, 'Logs')
    if not os.path.isdir(logs_dir):
        os.mkdir(logs_dir)
    cnf_dir = os.path.join(logs_dir, options.name)
    if not os.path.isdir(cnf_dir):
        os.mkdir(cnf_dir)
    params_dir = os.path.join(cnf_dir,
                              str(options.order_type) +
                              '_sc' + str(options.separate_construction) +
                              '_np' + str(options.numprocess) +
                              '_pbi' + str(options.pbintervals) +
                              '_ao' + str(options.applyonly) +
                              '_ep' + str(options.ep_flag) +
                              str(options.ep_order) +
                              '_sdjdp' + str(options.sep_djd_prep) +
                              '_preptl' + str(options.djd_prep_time_limit))
    if not os.path.isdir(params_dir):
        os.mkdir(params_dir)
    timedir = os.path.join(params_dir, datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    if not os.path.isdir(timedir):
        os.mkdir(timedir)
    return timedir + '/'


def ParseOptions(params):
    options = Options()
    options.path = params.file
    options.dir, options.filename = SplitFilename(options.path)
    options.name, options.suffix = SplitFileSuffix(options.filename)
    options.source_type = params.source
    options.order_type = params.order
    options.analyze_log = params.analyze_log
    options.analyze_var_limit = params.analyze_var_limit
    options.analyze_var_fraction = params.analyze_var_fraction
    options.run_tests = params.runtests
    options.show_statistic = params.show_stats
    options.show_version = params.show_ver
    options.show_options = False if (params.show_options in [False, 'False', 0, '0']) else True
    options.bdd_convert = False if (params.bdd_convert in [False, 'False', 0, '0']) else True
    options.test_bdd_convert = False if (params.test_bdd_convert in [False, 'False', 0, '0']) else True
    options.separate_construction = False if (params.separate_construction in [False, 'False', 0, '0']) else True
    options.redir_paths = False if params.redirpaths in [False, 'False', 0, '0'] else True
    options.djd_prep = False if params.djd_prep in [False, 'False', 0, '0'] else True
    options.lock_vars = False if params.lockvars in [False, 'False', 0, '0'] else True
    options.numprocess = params.numproc
    options.pbintervals = params.pbintervals
    options.applyonly = params.applyonly
    options.pbiorder = params.pbiorder
    options.ep_flag = params.ep_flag
    options.ep_order = params.ep_order
    options.sep_djd_prep = params.sep_djd_prep
    options.djd_prep_time_limit = params.djd_prep_time_limit
    options.prepbinmode = params.prepbinmode
    options.bdd_max_size = params.bdd_max_size
    return options


def PrintOptions(options):
    print('Options:')
    print('Number of processes:', options.numprocess)
    print('Full path:', options.path)
    # print('Directory:', options.dir)
    print('Filename:', options.filename)
    # print('Name only:', options.name)
    # print('Suffix:', options.suffix)
    print('Source type:', options.source_type)
    print('Order:', options.order_type)
    # print('Analyze log:', options.analyze_log)
    # print('Analyze var limit:', options.analyze_var_limit)
    # print('Analyze var fraction:', options.analyze_var_fraction)
    print('Run tests:', options.run_tests)
    print('Show statistics:', options.show_statistic)
    print('Show version:', options.show_version)
    print('Show options:', options.show_options)
    print('Convert to BDD:', options.bdd_convert)
    print('Redirecting pathes:', options.redir_paths)
    print('DJD preprocessing:', options.djd_prep)
    print('Separate DJD-preprocessing:', options.sep_djd_prep)
    print('Binarization mode for preprocessing:', options.prepbinmode)
    print('Time limit for single path in DJD-preprocessing:', options.djd_prep_time_limit)
    print('Maximum BDD size:', options.bdd_max_size)
    print('Lock variables:', options.lock_vars)
    print('Number of Pseudo-Boolean Intervals:', options.pbintervals)
    print('Order for solving PBIs:', options.pbiorder)
    print('APPLY only mode:', options.applyonly)
    print('Existential projection mode:', options.ep_flag)
    print('Order for variables to EP:', options.ep_order)
    print()

