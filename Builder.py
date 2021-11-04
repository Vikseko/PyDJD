from Utils import *


class DisjunctiveDiagramsBuilder:
    def __init__(self, dnf, order, problem_type):
        self.problem_ = dnf
        self.order_ = order
        self.lit_less_ = order
        self.clause_less_ = order
        self.problem_type_ = problem_type
        self.diagram_node_less_ = None
        self.hash_ = None

    def BuildDiagram(self):
        diagram_ = DisjunctiveDiagram()
        diagram_.problem_type_ = self.problem_type_
        ranges = []
        for idx in range(len(self.problem_)):
            self.problem_[idx] = DisjunctiveDiagramsBuilder.LitLessSort(order=self.order_,lits=self.problem_[idx])
            ranges.append([idx,0,len(self.problem_[idx])])
        root_set = DisjunctiveDiagramsBuilder.BuildDiagramNodes(self,ranges,diagram_)
        diagram_.roots_.update(root_set)
        for node in diagram_.roots_:
            node.node_type = DiagramNodeType.RootNode
        DisjunctiveDiagramsBuilder.FillParents(diagram_)
        DisjunctiveDiagramsBuilder.FixRoots(diagram_)
        DisjunctiveDiagramsBuilder.EnumerateDiagramNodes(diagram_)
        return diagram_

    def BuildDiagramNodes(self,ranges:list,diagram_):
        # Определим множество уникальных переменных в текущем фрагменте
        var_set = SortedSet()
        for range in ranges:
            var_set.add(abs(self.problem_[range[0]][range[1]]))
        nodes = set()
        for var_id in var_set:
            high_range = []
            low_range = []
            has_high_terminal = False
            has_low_terminal = False
            # Заполняем high_range и low_range
            for range in ranges:
                lit = self.problem_[range[0]][range[1]]
                if var_id == abs(lit):
                    phase = True if lit > 0 else False
                    if phase:
                        if has_high_terminal:
                            continue
                        if range[1]+1 == range[2]:
                            has_high_terminal = True
                            high_range.clear()
                            continue
                        #range[1] += 1
                        high_range.append([range[0],range[1] + 1,range[2]])
                    else:
                        if has_low_terminal:
                            continue
                        if range[1]+1 == range[2]:
                            has_low_terminal = True
                            low_range.clear()
                            continue
                        #range[1] += 1
                        low_range.append([range[0],range[1] + 1,range[2]])
            # Строим high-потомков
            high_nodes = set()
            if has_high_terminal:
                high_nodes.add(diagram_.GetTrueLeaf())
            elif len(high_range)>0:
                high_nodes = DisjunctiveDiagramsBuilder.BuildDiagramNodes(self,high_range,diagram_)
            if len(high_nodes) == 0:
                high_nodes.add(diagram_.GetQuestionLeaf())
            # Строим low-потомков
            low_nodes = set()
            if has_low_terminal:
                low_nodes.add(diagram_.GetTrueLeaf())
            elif len(low_range)>0:
                low_nodes = DisjunctiveDiagramsBuilder.BuildDiagramNodes(self,low_range,diagram_)
            if len(low_nodes) == 0:
                low_nodes.add(diagram_.GetQuestionLeaf())
            # Создаем узел диаграммы
            node = DiagramNode(DiagramNodeType.InternalNode, var_id, list(high_nodes), list(low_nodes))
            node = DisjunctiveDiagramsBuilder.AddDiagramNode(node,diagram_)
            nodes.add(node)
            diagram_.var_set_.add(var_id)
        return nodes

    def FillParents(diagram:DisjunctiveDiagram):
        for node in diagram.table_:
            for c_node in node.high_childs:
                c_node.high_parents.append(node)
            for c_node in node.low_childs:
                c_node.low_parents.append(node)

    def FixRoots(diagram:DisjunctiveDiagram):
        for node in diagram.table_:
            if len(node.low_parents) != 0 or len(node.high_parents) != 0:
                if node.node_type == DiagramNodeType.RootNode:
                    #print('ERROR INTERNAL ROOT')
                    node.node_type = DiagramNodeType.InternalNode

    def AddDiagramNode(node:DiagramNode,diagram_):
        if node in diagram_.table_:
            it_node = get_equivalent(diagram_.table_,node)
            del node
            return it_node
        else:
            node.HashKey()
            diagram_.table_.add(node)
            return node

    def EnumerateDiagramNodes(diagram:DisjunctiveDiagram):
        vertex_id = 0
        for node in diagram.table_:
            vertex_id += 1
            node.vertex_id = vertex_id


    def LitLessSort(order:list, lits:list):
        abslits = [abs(x) for x in lits]
        litsorder = [x for x in order if x in abslits]
        litsorder.reverse()
        for i in range(len(litsorder)):
            litsorder[i] = (-1) * litsorder[i] if ((-1) * litsorder[i]) in lits else litsorder[i]
        return litsorder

    def ClauseLessSort(self,):
        pass

    def __del__(self):
        del self


