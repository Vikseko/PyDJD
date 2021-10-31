from Types import *

def ExtractVarSet(problem, var_set):
    pass

def ExtractVarCounterMap(problem, var_map):
    pass

#Минимальный и максимальный номер переменной
def GetMinMaxVars(problem, min_var_id, max_var_id):
    pass

#азделить путь к папке и имя файла
def SplitFilename(path, dir, filename):
    pass

#Разделить имя файла на имя и суффикс
def SplitFileSuffix(filename, name, suffix):
    pass

#Проверяем существование файла
def FileExists(filename):
    pass

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
    pass

# Отрицание формулы. Применяется для перехода от КНФ конфликтных баз к ДНФ.
def NegateProblem(problem):
    pass

def ParseOptions(argc, argv, options):
    pass

def PrintOptions(out, options):
    pass

def PrintHelp(out):
    pass