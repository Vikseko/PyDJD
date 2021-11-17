from Builder import *
from Parser import *
from Pathfinder import *


if __name__ == '__main__':
    start_time = time.time()
    parser = createParser()
    options = ParseOptions(parser.parse_args(sys.argv[1:]))
    if options.show_version:
        print('PyDJD Version 1.0, October 2021')
    if options.show_options:
        PrintOptions(options)
    if (not FileExists(options)):
        raise RuntimeError('File', options.filename, 'doesn\'t exist in directory', options.dir)
    print('Problem:'.ljust(30,' '), options.filename)
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
    print('Number of vertices:'.ljust(30,' '), len(diagram.table_))
    print('Number of roots:'.ljust(30,' '), len(diagram.roots_))
    print('DiagramNode constructors:'.ljust(30,' '), DiagramNode.constructors_)
    print('DiagramNode destructors:'.ljust(30,' '), DiagramNode.destructors_)
    build_time = time.time() - start_build_time
    print('Build time:'.ljust(30,' '), build_time)

