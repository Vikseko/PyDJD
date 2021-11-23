from Builder import *
from Parser import *
from Pathfinder import *
from Redirection import *


if __name__ == '__main__':
    start_time = time.time()
    print('Start building procedure:')
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
    new_cnf, tmp_ = GetCNFFromDiagram(diagram)
    new_cnf = CNF(from_clauses=new_cnf)
    new_cnf.to_file('Logs/beforeprep_' + options.name + '.cnf')
    print()
    if options.redir_paths == True:
        start_redir_time = time.time()
        print('Start redirection procedure:')
        #PathsRedirection(diagram,problem)
        RedirectQuestionPathsFromDiagram(diagram)
        print('Number of vertices:'.ljust(30, ' '), len(diagram.table_))
        print('DiagramNode constructors:'.ljust(30,' '), DiagramNode.constructors_)
        print('DiagramNode destructors:'.ljust(30, ' '), DiagramNode.destructors_)
        redir_time = time.time() - start_redir_time
        print('Redirecting time:'.ljust(30, ' '), redir_time)
        print()
        print('Total runtime'.ljust(30,' '), time.time() - start_time)
        new_cnf, tmp_ = GetCNFFromDiagram(diagram)
        new_cnf = CNF(from_clauses=new_cnf)
        #solver = MapleChrono(bootstrap_with=new_cnf)
        #s = solver.solve()
        #if s == True:
            #print('still broken')
        new_cnf.to_file('Logs/djdprep_'+options.name+'.cnf')
