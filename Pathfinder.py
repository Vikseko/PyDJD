from Utils import *
from Builder import DisjunctiveDiagramsBuilder
from Redirection import *

# Получаем КНФ из диаграммы (все пути из корней в терминальную 'true')
def GetCNFFromDiagram(diagram:DisjunctiveDiagram):
    cnf = []
    node_paths = []
    true_leaf = diagram.GetTrueLeaf()
    for node in true_leaf.high_parents:
        clause = []
        clause.append(node.var_id)
        node_path = []
        node_path.append(node)
        WritePaths(cnf,node_paths,node_path,clause)
    for node in true_leaf.low_parents:
        clause = []
        clause.append(-node.var_id)
        node_path = []
        node_path.append(node)
        WritePaths(cnf,node_paths,node_path,clause)
    NegateProblem(cnf)
    return cnf,node_paths

# Получаем ДНФ из диаграммы (все пути из корней в терминальную 'true')
def GetDNFFromDiagram(diagram:DisjunctiveDiagram):
    dnf = []
    node_paths = []
    true_leaf = diagram.GetTrueLeaf()
    for node in true_leaf.high_parents:
        clause = []
        clause.append(node.var_id)
        node_path = []
        node_path.append(node)
        WritePaths(dnf,node_paths,node_path,clause)
    for node in true_leaf.low_parents:
        clause = []
        clause.append(-node.var_id)
        node_path = []
        node_path.append(node)
        WritePaths(dnf,node_paths,node_path,clause)
    return dnf,node_paths

# Получаем false paths из диаграммы (все пути из корней в терминальную '?')
def GetQuestionPathsFromDiagram(diagram:DisjunctiveDiagram):
    question_paths = []
    node_paths = []
    question_leaf = diagram.GetQuestionLeaf()
    for node in question_leaf.high_parents:
        clause = []
        clause.append(node.var_id)
        node_path = []
        node_path.append(node)
        WritePaths(question_paths,node_paths,node_path,clause)
    for node in question_leaf.low_parents:
        clause = []
        clause.append(-node.var_id)
        node_path = []
        node_path.append(node)
        WritePaths(question_paths,node_paths,node_path,clause)
    return question_paths,node_paths

def WritePaths(problem,node_paths,node_path,clause):
    current_node:DiagramNode = node_path[-1]
    if current_node.IsRoot():
        clause.reverse()
        node_path.reverse()
        problem.append(clause)
        node_paths.append(node_path)
    else:
        for node in current_node.high_parents:
            hclause = copy.copy(clause)
            hnode_path = copy.copy(node_path)
            hclause.append(node.var_id)
            hnode_path.append(node)
            WritePaths(problem, node_paths, hnode_path, hclause)
        for node in current_node.low_parents:
            lclause = copy.copy(clause)
            lnode_path = copy.copy(node_path)
            lclause.append(-node.var_id)
            lnode_path.append(node)
            WritePaths(problem, node_paths, lnode_path, lclause)

# Получаем false paths из диаграммы (все пути из корней в терминальную '?')
def RedirectQuestionPathsFromDiagram(diagram:DisjunctiveDiagram):
    question_paths = []
    cnf, tmp_ = GetCNFFromDiagram(diagram)
    cnf = CNF(from_clauses=cnf)
    g = MapleChrono(bootstrap_with=cnf)
    question_leaf = diagram.GetQuestionLeaf()
    for node in question_leaf.high_parents:
        clause = []
        clause.append(node.var_id)
        node_path = []
        node_path.append(node)
        RedirPaths(question_paths,node_path,clause, g, diagram)
    for node in question_leaf.low_parents:
        clause = []
        clause.append(-node.var_id)
        node_path = []
        node_path.append(node)
        RedirPaths(question_paths,node_path,clause, g, diagram)
    return question_paths

def RedirPaths(problem,node_path,clause, g, diagram):
    current_node:DiagramNode = node_path[-1]
    if current_node.IsRoot():
        clause.reverse()
        node_path.reverse()
        #problem.append(clause)
        #node_paths.append(node_path)
        s, model = PathCheck(clause, g)
        if s == False:
            flag_copy_path = RedirectPath(clause, node_path, diagram)
            if flag_copy_path == True:
                nof_redir_copy_paths += 1
            else:
                nof_redir_uniq_paths += 1
        if s == None:
            pass
        if s == True:
            # print('Problem solved due false path checking.')
            # print('Model:', model)
            # break
            pass
    else:
        for node in current_node.high_parents:
            hclause = copy.copy(clause)
            hnode_path = copy.copy(node_path)
            hclause.append(node.var_id)
            hnode_path.append(node)
            WritePaths(problem, node_paths, hnode_path, hclause)
        for node in current_node.low_parents:
            lclause = copy.copy(clause)
            lnode_path = copy.copy(node_path)
            lclause.append(-node.var_id)
            lnode_path.append(node)
            WritePaths(problem, node_paths, lnode_path, lclause)