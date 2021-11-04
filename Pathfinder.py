from Utils import *
from Builder import DisjunctiveDiagramsBuilder

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

# Получаем ДНФ из диаграммы (все пути из корней в терминальную 'true')
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