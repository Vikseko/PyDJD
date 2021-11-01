from Builder import *
import sys
import argparse
import time
# Press Shift+F10 to execute it.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

#Parser
def createParser ():
    parser = argparse.ArgumentParser()
    parser.add_argument ('-f', '--file', nargs='?', type=str, default='Tests/test1.cnf')
    parser.add_argument ('-o', '--order', nargs='?', type=str, default='cnf')
    parser.add_argument ('-s', '--source', nargs='?', type=str, default='direct')
    parser.add_argument('-rt', '--runtests', nargs='?', type=bool, default=False)
    parser.add_argument('-ss', '--show_stats', nargs='?', type=bool, default=False)
    parser.add_argument('-sv', '--show_ver', nargs='?', type=bool, default=False)
    parser.add_argument ('-so', '--show_options', nargs='?', type=bool, default=False)
    parser.add_argument ('-rp', '--redirpaths', nargs='?', type=bool, default=False)
    parser.add_argument('-lv', '--lockvars', nargs='?', type=bool, default=False)
    parser.add_argument('-al', '--analuze_log', nargs='?', type=str, default='')
    parser.add_argument('-avl', '--analyze_var_limit', nargs='?', type=int, default=20)
    parser.add_argument('-avf', '--analyze_var_fraction', nargs='?', type=float, default=0.5)
    return parser


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    start_time = time.time()
    parser = createParser()
    options = ParseOptions(parser.parse_args(sys.argv[1:]))

    if options.show_version:
        print('Version 0.9, October 2021')
    if options.show_options:
        PrintOptions(options)

    if (not FileExists(options.path)):
        raise RuntimeError('File', options.filename, 'doesn\'t exist in directory', options.dir)
    problem, order = ReadProblem(options)
    if len(order) == 0:
        raise RuntimeError('Order is empty')
    # Журнализируем текущий порядок переменных
    with open('Logs/order.log','w') as orderf:
        print(*order,file=orderf)
    # Строим отрицание считанной формулы(КНФ= > ДНФ)
    if (options.source_type == "conflicts" or options.source_type == "cnf"):
        NegateProblem(problem)

    start_build_time = time.time()
    builder = DisjunctiveDiagramsBuilder(problem, order, GetProblemType(options.source_type))
    diagram = builder.BuildDiagram()
    build_time = time.time() - start_build_time