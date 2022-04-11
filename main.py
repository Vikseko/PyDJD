from Builder import *
from Parser import *
from Pathfinder import *
from Redirection import *
#from BDD_converter import *

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
    before_cnf, tmp_ = GetCNFFromDiagram(diagram)
    before_cnf = CNF(from_clauses=SortClausesInCnf(before_cnf))
    before_cnf.to_file('Logs/' + options.name + '_before.cnf')
    #DisjunctiveDiagram.PrintCurrentTable(diagram)
    print()

    if options.djd_prep == True:
        start_djdprep = time.time()
        print('Start preprocessing procedure:')
        all_question_pathes = CountQuestionPathsInDiagram(diagram)
        question_paths_count = len(all_question_pathes)
        print('Number of question paths:'.ljust(30,' '), question_paths_count)
        new_cnf = CheckPaths(diagram,all_question_pathes)
        djd_prep_time = time.time() - start_djdprep
        print('Preprocessing time:'.ljust(30, ' '), djd_prep_time)
        print()
        print('Total runtime'.ljust(30,' '), time.time() - start_time)
        new_cnf = CNF(from_clauses=SortClausesInCnf(new_cnf.clauses))
        new_cnf.to_file('Logs/' + options.name + '_djdprep_v4.cnf')

    if options.redir_paths == True:
        start_redir_time = time.time()
        print('Start redirection procedure:')
        question_paths_count = len(CountQuestionPathsInDiagram(diagram))
        print('Number of question paths:'.ljust(30,' '), question_paths_count)
        # v1, нужно закомментить from Redirection import * в Pathfinder.py
        # в этой версии сперва собираются все пути, затем скопом обрабатываются
        #PathsRedirection(diagram,problem)
        # v2, нужно раскомментить from Redirection import * в Pathfinder.py
        # в этой версии каждый путь находит отдельно и обрабатывается сразу
        # но часть путей может пропустить
        RedirectQuestionPathsFromDiagram(diagram)
        # v3 тут пути обрабатываются по одному за раз, как в v2, но не узлы помечаются посещенными
        # а сам путь (литералы) запоминается в хэш таблице и если такой уже есть в ней, то не обрабатывается
        #RedirectQuestionPathsFromDiagram_v3(diagram, question_paths_count)
        print('Number of vertices:'.ljust(30, ' '), len(diagram.table_))
        print('DiagramNode constructors:'.ljust(30,' '), DiagramNode.constructors_)
        print('DiagramNode destructors:'.ljust(30, ' '), DiagramNode.destructors_)
        if DiagramNode.destructor_errors_ > 0:
            print('DiagramNode errors in destructors:'.ljust(30, ' '), DiagramNode.destructor_errors_)
        redir_time = time.time() - start_redir_time
        print('Redirecting time:'.ljust(30, ' '), redir_time)
        print()
        print('Total runtime'.ljust(30,' '), time.time() - start_time)
        after_cnf, tmp_ = GetCNFFromDiagram(diagram)
        after_cnf = CNF(from_clauses=after_cnf)
        after_cnf.to_file('Logs/' + options.name + '_djdprep_v2.cnf')

    if options.bdd_convert == True:
        start_bdd_time = time.time()
        print('Start \"DJD_to_BDD\" procedure:')
        bdd_diagram = BDDiagram(diagram)
        print('Transition to BDD complete.')
        if BDDiagram.NonBinaryLinkCount(bdd_diagram) > 0:
            print('ERROR. Number of nonbinary link is', BDDiagram.NonBinaryLinkCount(bdd_diagram))
        else:
            print('Number of nonbinary link in diagram is', BDDiagram.NonBinaryLinkCount(bdd_diagram))
        BDDiagram.PrintCurrentTable(bdd_diagram)
        #after_cnf, tmp_ = GetCNFFromDiagram(bdd_diagram)
        #after_cnf = CNF(from_clauses=after_cnf)
        #after_cnf.to_file('Logs/bdd_convertion_' + options.name + '.cnf')
        print('Number of new nodes (during BDD-transformation):', bdd_diagram.new_nodes_)
        print('Number of deleted nodes (during BDD-transformation):', bdd_diagram.deleted_nodes_)
        print('Number of vertices:'.ljust(30, ' '), len(bdd_diagram.table_))
        print('DiagramNode constructors:'.ljust(30,' '), DiagramNode.constructors_)
        print('DiagramNode destructors:'.ljust(30, ' '), DiagramNode.destructors_)
        convert_time = time.time() - start_bdd_time
        print('Conversion time:'.ljust(30, ' '), convert_time)

