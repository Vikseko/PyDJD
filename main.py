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
    before_cnf, tmp_ = GetCNFFromDiagram(diagram)
    before_cnf = CNF(from_clauses=before_cnf)
    before_cnf.to_file('Logs/beforeprep_' + options.name + '.cnf')
    """var1 = 143
    var2 = 142
    for node in diagram.GetTrueLeaf().high_parents:
        if node.Value() == var1:
            print('1 ')
            print('1 find var1', var1,node)
            for cnode in node.high_parents:
                if cnode.Value() == var2:
                    print('1 ')
                    print('1 find var2', var2,cnode)
                    if cnode.node_type == DiagramNodeType.RootNode:
                        print('1 its root')
                    elif len(cnode.high_parents) + len(cnode.low_parents) == 0:
                        print('1 its not root but hasnt parents')
                    else:
                        print('1 its not root has parents', len(cnode.high_parents) + len(cnode.low_parents), ':', [(x.Value(),x.node_type) for x in cnode.low_parents],[(x.Value(),x.node_type) for x in cnode.high_parents])
    #print([x.Value() for x in diagram.GetTrueLeaf().high_parents],[x.Value() for x in diagram.GetTrueLeaf().low_parents])"""
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
        after_cnf, tmp_ = GetCNFFromDiagram(diagram)
        after_cnf = CNF(from_clauses=after_cnf)
        after_cnf.to_file('Logs/djdprep_' + options.name + '.cnf')

"""     solver = MapleChrono(bootstrap_with=after_cnf)
        timer = Timer(30, interrupt, [solver])
        timer.start()
        s = solver.solve_limited(expect_interrupt=True)
        solver.clear_interrupt()
        if s == True:
            print('still broken')
        

        #print([x.Value() for x in diagram.GetTrueLeaf().high_parents],
              #[x.Value() for x in diagram.GetTrueLeaf().low_parents])

        before_cnf_clauses = before_cnf.clauses
        after_cnf_clauses = after_cnf.clauses
        disappeared_clauses = []
        for clause in before_cnf_clauses:
            for clause2 in after_cnf_clauses:
                if len(set(clause).difference(set(clause2))) == 0:
                    break
            else:
                print('ERROR clause', clause, 'disappeared')
                disappeared_clauses.append(clause)
        #after_cnf.extend(disappeared_clauses)
        #solver2 = MapleChrono(bootstrap_with=after_cnf)
        #a = solver2.solve()
        #if a == True:
            #print('still broken')
        #clause = [x for x in disappeared_clauses if len(x) == 2][0]
        #print(clause)
        var1 = 143
        var2 = 142
        for node in diagram.GetTrueLeaf().high_parents:
            if node.Value() == var1:
                print('2 ')
                print('2 find var1',var1, node)
                for cnode in node.high_parents:
                    if cnode.Value() == var2:
                        print('2 ')
                        print('2 find var2',var2, cnode)
                        if cnode.node_type == DiagramNodeType.RootNode:
                            print('2 its root')
                        elif len(cnode.high_parents) + len(cnode.low_parents) == 0:
                            print('2 its not root but hasnt parents')
                        else:
                            print('2 its not root has parents', len(cnode.high_parents) + len(cnode.low_parents), ':', [(x.Value(),x.node_type) for x in cnode.low_parents],[(x.Value(),x.node_type) for x in cnode.high_parents])


    ERROR    clause[-142, -143]    disappeared
    ERROR    clause[-712, -713]    disappeared
    ERROR    clause[-1149, 1150, -1148]    disappeared
    ERROR    clause[-1198, 1199, -1197]    disappeared
    ERROR    clause[-1698, -1696]    disappeared
    ERROR    clause[-1874, -1875]    disappeared
    ERROR    clause[-2259, -2260]    disappeared
    ERROR    clause[-2685, -2686]    disappeared
"""