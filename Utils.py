from Types import *
from DimacsParser import *


def ReadProblem(options):
    lines = open(options.path,'r').readlines()
    problem, order, comments, var_count, lit_count, min_var_num, max_var_num = DimacsParser(lines)
    print('Lit count:'.ljust(30,' '), lit_count)
    print('Variables:'.ljust(30,' '), var_count)
    print('Lowest variable number:'.ljust(30,' '), min_var_num)
    print('Highest variable number:'.ljust(30,' '), max_var_num)
    if options.order_type == 'activity':
        print('Order:'.ljust(30,' '), 'activity')
        if order == None:
            raise RuntimeError('No activity order in DIMACS file')
        else:
            order.insert(0, 'true')
            order.insert(0, '?')
            return problem, order
    elif options.order_type == 'frequency':
        print('Order:'.ljust(30,' '), 'frequency')
        order = FrequencyOrder(problem,min_var_num,max_var_num)
    elif options.order_type == 'direct':
        print('Order:'.ljust(30,' '), 'direct')
        if max_var_num != 0:
            order = [x for x in reversed(range(1,max_var_num+1))]
        else:
            raise RuntimeError('No maximum variable found, check DIMACS file.')
    order.append('true')
    order.insert(0, '?')
    return problem, order, comments


def FrequencyOrder(problem,min_var_num, max_var_num):
    if min_var_num != 0 and max_var_num != 0:
        counter = [0 for x in range(max_var_num+1)]
        for clause in problem:
            for lit in clause:
                counter[abs(lit)] += 1
        counter = list(enumerate(counter))
        counter.sort(key=lambda x:x[1])
        counter.reverse()
        order = [x[0] for x in counter if x[1]>0]
        return order
    else:
        raise RuntimeError('No minimum and maximum variables found, check DIMACS file.')

def ExtractVarSet(problem, var_set):
    pass

def ExtractVarCounterMap(problem, var_map):
    pass

#Минимальный и максимальный номер переменной
def GetMinMaxVars(problem, min_var_id, max_var_id):
    pass

#азделить путь к папке и имя файла
def SplitFilename(path):
    if '\\' not in path:
        dir = ''.join(path.split('/')[:-1])
        filename = ''.join(path.split('/')[-1])
    else:
        dir = ''.join(path.split('\\')[:-1])
        filename = ''.join(path.split('\\')[-1])
    return dir,filename

#Разделить имя файла на имя и суффикс
def SplitFileSuffix(filename):
    name = ''.join(filename.split('.')[:-1])
    suffix = ''.join(filename.split('.')[-1])
    return name,suffix

#Проверяем существование файла
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
        type = ProblemType.Cnf
    elif str_type == 'dnf':
        type = ProblemType.Dnf
    elif str_type == 'conflict':
        type = ProblemType.Conflict
    else:
        raise RuntimeError('Unknown type of problem')
    return type

# Отрицание формулы. Применяется для перехода от КНФ конфликтных баз к ДНФ.
def NegateProblem(problem):
    for i in range(len(problem)):
        for j in range(len(problem[i])):
            problem[i][j] *= -1

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
    options.show_options = params.show_options
    options.bdd_convert = False if (params.bdd_convert in [False, 'False', 0, '0']) else True
    options.redir_paths = False if params.redirpaths in [False, 'False', 0, '0'] else True
    options.djd_prep = False if params.djd_prep in [False, 'False', 0, '0'] else True
    options.lock_vars = False if params.lockvars in [False, 'False', 0, '0'] else True
    return options

def PrintOptions(options):
    print('Options:')
    print('Full path:', options.path)
    #print('Directory:', options.dir)
    print('Filename:', options.filename)
    #print('Name only:', options.name)
    #print('Suffix:', options.suffix)
    print('Source type:', options.source_type)
    print('Order:', options.order_type)
    #print('Analyze log:', options.analyze_log)
    #print('Analyze var limit:', options.analyze_var_limit)
    #print('Analyze var fraction:', options.analyze_var_fraction)
    print('Run tests:', options.run_tests)
    print('Show statistics:', options.show_statistic)
    print('Show version:', options.show_version)
    print('Show options:', options.show_options)
    print('Convert to BDD:', options.bdd_convert)
    print('Redirecting pathes:', options.redir_paths)
    print('DJD preprocessing:', options.djd_prep)
    print('Lock variables:', options.lock_vars)
    print()

