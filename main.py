from Types import DiagramNode
from Types import DiagramNodeType
from Types import get_equivalent
from Types import DisjunctiveDiagram
import sys
# Press Shift+F10 to execute it.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print(DiagramNode.constructors_)
    TrueNode = DiagramNode(DiagramNodeType.TrueNode)
    FalseNode = DiagramNode(DiagramNodeType.FalseNode)
    QuestionNode = DiagramNode(DiagramNodeType.QuestionNode)
    Node = DiagramNode(DiagramNodeType.InternalNode,13,[FalseNode],[QuestionNode])
    Node2 = DiagramNode(DiagramNodeType.InternalNode,13,[FalseNode],[QuestionNode])
    Node3 = DiagramNode(DiagramNodeType.InternalNode, 12, [FalseNode], [QuestionNode])
    Node4 = DiagramNode(DiagramNodeType.InternalNode, 13, [QuestionNode], [FalseNode])
    print(DiagramNode.constructors_)
    print(Node.var_id)
    print(Node.node_type)
    if Node.node_type == DiagramNodeType.InternalNode:
        print('good')
    #print(type(Node.node_type))
    print(Node.Size())
    a = set()
    a.add(Node)
    print(len(a))
    if Node2 in a:
        print('finded')
        #Node_tmp = [node for node in a if node == Node2][0]
        Node_tmp = get_equivalent(a,Node2)
        print(Node_tmp == Node2, Node_tmp is Node2, Node_tmp == Node, Node_tmp is Node)
    a.add(Node2)
    print(len(a))
    print(Node.hash_key,Node2.hash_key,Node3.hash_key,Node4.hash_key)
    print(a)
    print('1',Node.__eq__(Node2))
    print('2',Node is Node2)
    print('3', Node == Node2)
    print('4',Node.__eq__(Node3))
    print('5',Node.__eq__(Node4))
    print('6',FalseNode.IsLeaf())
    print('7',Node.IsLeaf())
    print(FalseNode.hash_key, QuestionNode.hash_key, TrueNode.hash_key)
    print(FalseNode.Value(), QuestionNode.Value(), TrueNode.Value())

    diagram_ = DisjunctiveDiagram()
    trueleaf = diagram_.GetTrueLeaf()
    questionleaf = diagram_.GetQuestionLeaf()
    falseleaf = diagram_.GetFalseLeaf()
    print(falseleaf.hash_key, questionleaf.hash_key, trueleaf.hash_key)
    print(falseleaf.Value(), questionleaf.Value(), trueleaf.Value())
    print(DiagramNode.constructors_)