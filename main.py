from Builder import *
from Parser import *
from Pathfinder import *
# Press Shift+F10 to execute it.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


# Press the green button in the gutter to run the script.
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
    print('Problem:  ', options.filename)
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
    print('Number of vertices:', len(diagram.table_))
    print('Number of roots:', len(diagram.roots_))
    print('DiagramNode constructors:', DiagramNode.constructors_)
    print('DiagramNode destructors:', DiagramNode.destructors_)
    build_time = time.time() - start_build_time
    print('Build time:', build_time)
    #for node in diagram.table_:
        #print(node.Value(), node, node.node_type, [(x.Value(),x) for x in node.high_childs], [(x.Value(),x) for x in node.low_childs])


"""
    newcnf,paths_to_true = GetCNFFromDiagram(diagram)
    import pysat
    from pysat.solvers import Minisat22
    from pysat.formula import CNF

    NegateProblem(problem)
    orig_cnf = CNF(from_clauses=problem)
    new_cnf = CNF(from_clauses=newcnf)
    g = Minisat22(bootstrap_with=orig_cnf)
    s = Minisat22(bootstrap_with=new_cnf)
    g.solve()
    s.solve()
    mn = 0
    nm = 0
    for m in g.enum_models():
        mn += 1
        #(m)
    for n in s.enum_models():
        nm += 1
        #print(n)
    print(mn,nm)
    print(orig_cnf.clauses)
    print(new_cnf.clauses)"""
    # Fixme: нужно исправить ситуацию, когда переменные в формуле идут не по порядку, а с пропусками.

