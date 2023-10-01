from Builder import *
from Parser import *
from Pathfinder import *
from Redirection import *
# PYTHONHASHSEED=0 python3 main.py -f ./Tests/SumSimple1+1.cnf -o frequency -s cnf -bdd 1 -tbdd 0 -sc 1 -np 4

if __name__ == '__main__':
    start_time = time.time()
    if not os.path.isdir('./Logs/'):
        os.mkdir('./Logs/')
    print('Start building procedure:')
    parser = createParser()
    options = ParseOptions(parser.parse_args(sys.argv[1:]))
    if options.show_version:
        print('PyDJD Version 1.0, October 2021')
    if options.show_options:
        PrintOptions(options)
    if (not FileExists(options)):
        raise RuntimeError('File', options.filename, 'doesn\'t exist in directory', options.dir)
    print('Problem:'.ljust(30, ' '), options.filename)
    var_count, problem, order, problem_comments = ReadProblem(options)
    if len(order) == 0:
        raise RuntimeError('Order is empty')
    print('Order', order)
    # Журнализируем текущий порядок переменных
    with open('Logs/order.log', 'w') as orderf:
        print(*order, file=orderf)
    # Строим отрицание считанной формулы(КНФ= > ДНФ)
    if (options.source_type == "conflicts" or options.source_type == "cnf"):
        NegateProblem(problem)
    start_build_time = time.time()
    if options.separate_construction:
        diagrams = []
        problems = DivideProblem(problem, var_count, order)
        with multiprocessing.Pool(min(len(problems), options.numprocess)) as p:
        # p = multiprocessing.Pool(min(len(problems), options.numprocess))
            jobs = [p.apply_async(CreateDiagram, (var_count, problem, order, GetProblemType(options.source_type))) for
                    problem in problems]
            p.close()
            for job in jobs:
                diagrams.append(job.get())
            p.join()
        print('Number of diagrams:'.ljust(30, ' '), len(diagrams))
        print('Number of vertices:'.ljust(30, ' '), [len(diagram.table_) for diagram in diagrams])
        print('Number of roots:'.ljust(30, ' '), [len(diagram.roots_) for diagram in diagrams])
        print('DiagramNode constructors:'.ljust(30, ' '), DiagramNode.constructors_)
        print('DiagramNode destructors:'.ljust(30, ' '), DiagramNode.destructors_)
        build_time = time.time() - start_build_time
        print('Build time:'.ljust(30, ' '), build_time)
        for index, diagram in enumerate(diagrams):
            # diagram.PrintProblem()
            diagram.PrintCurrentTable('SubDJDiagram ' + str(index+1) + ':')
    else:
        diagram = CreateDiagram(var_count, problem, order, GetProblemType(options.source_type))
        print('Number of vertices:'.ljust(30, ' '), len(diagram.table_))
        print('Number of roots:'.ljust(30, ' '), len(diagram.roots_))
        print('DiagramNode constructors:'.ljust(30, ' '), DiagramNode.constructors_)
        print('DiagramNode destructors:'.ljust(30, ' '), DiagramNode.destructors_)
        build_time = time.time() - start_build_time
        print('Build time:'.ljust(30, ' '), build_time)
        before_cnf, tmp_ = GetCNFFromDiagram(diagram)
        before_cnf = CNF(from_clauses=SortClausesInCnf(before_cnf))
        before_cnf.to_file('Logs/' + options.name + '_before.cnf', comments=problem_comments)
        diagram.PrintCurrentTable()
        # print(diagram.GetRoots())
        current_roots_ = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_, diagram.roots_)
        print('Roots:', [str(x.vertex_id) + '_' + str(x.var_id) for x in current_roots_])
        # DrawDiagram(diagram)
        print()

    if (not options.separate_construction) and options.djd_prep:
        start_djdprep = time.time()
        print('Start preprocessing procedure:')
        all_question_pathes = CountQuestionPathsInDiagram(diagram)
        question_paths_count = len(all_question_pathes)
        print('Number of question paths:'.ljust(30, ' '), question_paths_count)
        new_cnf = CheckPaths(diagram, all_question_pathes)
        djd_prep_time = time.time() - start_djdprep
        print('Preprocessing time:'.ljust(30, ' '), djd_prep_time)
        print()
        print('Total runtime'.ljust(30, ' '), time.time() - start_time)
        new_cnf = CNF(from_clauses=SortClausesInCnf(new_cnf.clauses))
        new_cnf.to_file('DJD_prep_cnfs_1sec/djdprep_' + options.name + '.cnf', comments=problem_comments)

    if (not options.separate_construction) and options.redir_paths:
        start_redir_time = time.time()
        print('Start redirection procedure:')
        question_paths_count = len(CountQuestionPathsInDiagram(diagram))
        print('Number of question paths:'.ljust(30, ' '), question_paths_count)
        # v1, нужно закомментить from Redirection import * в Pathfinder.py
        # в этой версии сперва собираются все пути, затем скопом обрабатываются
        # PathsRedirection(diagram,problem)
        # v2, нужно раскомментить from Redirection import * в Pathfinder.py
        # в этой версии каждый путь находит отдельно и обрабатывается сразу
        # но часть путей может пропустить
        RedirectQuestionPathsFromDiagram(diagram)
        # v3 тут пути обрабатываются по одному за раз, как в v2, но не узлы помечаются посещенными
        # а сам путь (литералы) запоминается в хэш таблице и если такой уже есть в ней, то не обрабатывается
        # RedirectQuestionPathsFromDiagram_v3(diagram, question_paths_count)
        print('Number of vertices:'.ljust(30, ' '), len(diagram.table_))
        print('DiagramNode constructors:'.ljust(30, ' '), DiagramNode.constructors_)
        print('DiagramNode destructors:'.ljust(30, ' '), DiagramNode.destructors_)
        if DiagramNode.destructor_errors_ > 0:
            print('DiagramNode errors in destructors:'.ljust(30, ' '), DiagramNode.destructor_errors_)
        redir_time = time.time() - start_redir_time
        print('Redirecting time:'.ljust(30, ' '), redir_time)
        print()
        print('Total runtime'.ljust(30, ' '), time.time() - start_time)
        after_cnf, tmp_ = GetCNFFromDiagram(diagram)
        after_cnf = CNF(from_clauses=after_cnf)
        after_cnf.to_file('Logs/' + options.name + '_djdprep_v2.cnf', comments=problem_comments)

    if options.bdd_convert:
        from BDD_converter import *
        # from Test_diagram import *
        start_bdd_time = time.time()
        print('Start transition to BDD.')
        if not options.separate_construction:
            bdd_diagram, transform_time_ = DJDtoBDD(diagram)
            EnumerateBDDiagramNodes(bdd_diagram)
            print('Transition to BDD complete.')
            if BDDiagram.NonBinaryLinkCount(bdd_diagram) > 0:
                print('ERROR. Number of nonbinary link is', bdd_diagram.NonBinaryLinkCount())
            else:
                print('Number of nonbinary link in diagram is', bdd_diagram.NonBinaryLinkCount())
            bdd_diagram.PrintCurrentTable('Final table:')
            if len(bdd_diagram.table_sizes) < 1000:
                print('Changes of number of vertices in diagram:', bdd_diagram.table_sizes)
            if len(bdd_diagram.table_sizes) > 1:
                print('Number of removed nonbinary links:', len(bdd_diagram.table_sizes) - 1)
                print('Initial size of diagram:', bdd_diagram.table_sizes[0])
                print('Final size of diagram:', bdd_diagram.table_sizes[-1])
                print('Max size of diagram:', max(bdd_diagram.table_sizes))
                print('Min size of diagram:', min(bdd_diagram.table_sizes))
                print('Avg size of diagram:', mean(bdd_diagram.table_sizes))
                print('Median size of diagram:', median(bdd_diagram.table_sizes))
                print('Sd of size of diagram:', round(math.sqrt(variance(bdd_diagram.table_sizes)), 2))
            # DrawDiagram(bdd_diagram)
        else:
            bdd_diagram = DJDtoBDD_separated(diagrams, options.numprocess, order)
            print('Multiprocessing transition to BDD complete.')
            if BDDiagram.NonBinaryLinkCount(bdd_diagram) > 0:
                print('ERROR. Number of nonbinary link is', bdd_diagram.NonBinaryLinkCount())
            else:
                print('Number of nonbinary link in diagram is', bdd_diagram.NonBinaryLinkCount())
            # DrawDiagram(bdd_diagram)
        if len(bdd_diagram.table_) > 0:
            paths_to_true, tmp_ = bdd_diagram.GetPathsToTrue()
            WritePathsToFile(paths_to_true, 'Logs/' + options.name + '_bdd_convertion.true_paths')
            sat_assigments, tmp2_ = bdd_diagram.GetSatAssignmentFromDiagram()
            WritePathsToFile(sat_assigments, 'Logs/' + options.name + '_bdd_convertion.sat_assignments')
            bdd_diagram.PrintCurrentTableJSON('Logs/' + options.name + '_bdd_convertion.json')
            bdd_cnf, tmp3_ = bdd_diagram.GetCNFFromBDD()
            bdd_cnf = CNF(from_clauses=bdd_cnf)
            bdd_cnf.to_file('Logs/' + options.name + '_bdd_convertion.cnf', comments=problem_comments)
        print('Number of new nodes (during BDD-transformation):', bdd_diagram.new_nodes_)
        print('Number of deleted nodes (during BDD-transformation):', bdd_diagram.deleted_nodes_)
        print('Number of actions with links (during BDD-transformation):', bdd_diagram.actions_with_links_)
        print('Number of vertices:'.ljust(30, ' '), len(bdd_diagram.table_))
        print('DiagramNode constructors:'.ljust(30, ' '), DiagramNode.constructors_)
        print('DiagramNode destructors:'.ljust(30, ' '), DiagramNode.destructors_)
        convert_time = time.time() - start_bdd_time
        print('Conversion time:'.ljust(30, ' '), convert_time)
        if len(bdd_diagram.table_) > 0:
            if 10000 >= len(sat_assigments) > 0 and options.source_type == 'cnf':
                print('\nSAT assignments for initial CNF:')
                for sat_assigment in sat_assigments:
                    print('Satisfiable assignment:', sorted(sat_assigment, key=lambda x: abs(x)))
        if options.test_bdd_convert:
            from Test_diagram import *
            start_testing_time = time.time()
            print('\nStart testing BDD.')
            nof_inputs, false_paths, true_paths = test_bdd(bdd_diagram)
            print('Total checked inputs:', nof_inputs)
            print('Number of paths to 1-vertex:', true_paths)
            print('Number of paths to 0-vertex:', false_paths)
            testing_time = time.time() - start_testing_time
            print('Testing time:'.ljust(30, ' '), testing_time)
