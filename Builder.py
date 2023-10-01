from Utils import *


def CreateDiagram(params):
    var_count = params[0]
    dnf = params[1]
    order = params[2]
    problem_type = params[3]
    return DisjunctiveDiagramsBuilder(var_count, dnf, order, problem_type).diagram_


class DisjunctiveDiagramsBuilder:
    def __init__(self, var_count, dnf, order, problem_type):
        self.variable_count_ = var_count
        self.problem_ = dnf
        self.order_ = order
        self.lit_less_ = order
        self.clause_less_ = order
        self.problem_type_ = problem_type
        self.nodes_with_changed_hash = set()
        self.diagram_node_less_ = None
        self.hash_ = None
        self.diagram_ = self.BuildDiagram()

    def BuildDiagram(self):
        diagram_ = DisjunctiveDiagram()
        diagram_.problem_type_ = self.problem_type_
        diagram_.order_ = self.order_
        diagram_.variable_count_ = self.variable_count_
        ranges = []
        for idx in range(len(self.problem_)):
            self.problem_[idx] = DisjunctiveDiagramsBuilder.LitLessSort(order=self.order_,lits=self.problem_[idx])
            ranges.append([idx,0,len(self.problem_[idx])])
        root_set = DisjunctiveDiagramsBuilder.BuildDiagramNodes(self,ranges,diagram_)
        diagram_.roots_.update(root_set)
        DisjunctiveDiagramsBuilder.FillParents(diagram_)
        #print('Before consuming subtrees')
        #DisjunctiveDiagram.PrintCurrentTable(diagram_)
        DisjunctiveDiagramsBuilder.ConsumingSubtrees(self,diagram_)
        #print('After consuming subtrees')
        #DisjunctiveDiagram.PrintCurrentTable(diagram_)
        DisjunctiveDiagramsBuilder.EnumerateDiagramNodes(diagram_)
        return diagram_

    def BuildDiagramNodes(self, ranges:list, diagram_, reclevel=0):
        # Определим множество уникальных переменных в текущем фрагменте
        var_set = set()
        for range in ranges:
            var_set.add(abs(self.problem_[range[0]][range[1]]))
        var_set = SortedSet(var_set)
        nodes = set()
        for var_id in var_set:
            high_range = []
            low_range = []
            has_high_terminal = False
            has_low_terminal = False
            # Заполняем high_range и low_range индексами из списка
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
                        high_range.append([range[0],range[1] + 1,range[2]])
                    else:
                        if has_low_terminal:
                            continue
                        if range[1]+1 == range[2]:
                            has_low_terminal = True
                            low_range.clear()
                            continue
                        low_range.append([range[0],range[1] + 1,range[2]])
            # Строим high-потомков
            high_nodes = set()
            if has_high_terminal:
                high_nodes.add(diagram_.GetTrueLeaf())
            elif len(high_range)>0:
                high_nodes = DisjunctiveDiagramsBuilder.BuildDiagramNodes(self,high_range,diagram_, reclevel=reclevel+1)
            if len(high_nodes) == 0:
                high_nodes.add(diagram_.GetQuestionLeaf())
            # Строим low-потомков
            low_nodes = set()
            if has_low_terminal:
                low_nodes.add(diagram_.GetTrueLeaf())
            elif len(low_range)>0:
                low_nodes = DisjunctiveDiagramsBuilder.BuildDiagramNodes(self,low_range,diagram_, reclevel=reclevel+1)
            if len(low_nodes) == 0:
                low_nodes.add(diagram_.GetQuestionLeaf())
            # Создаем узел диаграммы
            if reclevel == 0:
                node = DiagramNode(DiagramNodeType.RootNode, var_id, list(high_nodes), list(low_nodes))
            else:
                node = DiagramNode(DiagramNodeType.InternalNode, var_id, list(high_nodes), list(low_nodes))
            node = DisjunctiveDiagramsBuilder.AddDiagramNode(node,diagram_)
            nodes.add(node)
            diagram_.var_set_.add(var_id)
        #print('Level', reclevel)
        #print('Nodes:', [(x.vertex_id, x.var_id, x.node_type) for x in nodes])
        return nodes

    def FillParents(diagram:DisjunctiveDiagram):
        for node in diagram.table_.values():
            for c_node in node.high_childs:
                c_node.high_parents.append(node)
            for c_node in node.low_childs:
                c_node.low_parents.append(node)

    # Некоторые узлы помечаются как корни, хотя у них есть родители
    # Суть данной проблемы в том, что когда поддерево вклеивается в диаграмму, то оно может
    # поглотить часть диаграммы. Корень поддерева всегда должен быть корнем диаграммы
    def ConsumingSubtrees(self, diagram:DisjunctiveDiagram):
        #real_roots = set()
        current_roots_ = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_, diagram.roots_)
        #print('Sorted roots 1:', [(x.vertex_id, x.var_id, x.node_type) for x in current_roots_])
        for root in current_roots_:
            # перебираем все корни
            # для каждого проверяем, есть ли в таблице внутренний узел с таким хэшем
            # какой был бы у корня, будь он внутренним
            # если есть, то он поглощается поддеревом, стартующим с корня
            internal_hash = [root.Value()]
            internal_hash += sorted([node.hash_key for node in root.high_childs])
            internal_hash += sorted([node.hash_key for node in root.low_childs])
            internal_hash += ['internal']
            internal_hash = hash(tuple(internal_hash))
            if internal_hash in diagram.table_:
                consumed_node: DiagramNode = diagram.table_[internal_hash]
                print('Root:', root.vertex_id, root.var_id, root.node_type)
                print('Consumed node:', consumed_node.vertex_id, consumed_node.var_id, consumed_node.node_type)
                DisjunctiveDiagramsBuilder.ConsumeSubtree(self,diagram,root,consumed_node)
            # nodes_for_check = OrderedSet()
            # nodes_for_check.update(root.high_parents)
            # nodes_for_check.update(root.low_parents)
            # root.high_parents.clear()
            # root.low_parents.clear()
            # deleted_nodes = set()
            # DisjunctiveDiagramsBuilder.CheckNodesForDelRootGluing(nodes_for_check, root, diagram, deleted_nodes)
        #print('Sorted roots 2:', [(x.vertex_id, x.var_id, x.node_type) for x in current_roots_])

    def ConsumeSubtree(self, diagram:DisjunctiveDiagram, root, consumed_node):
        # поглощение поддерева, выходящего из узла consumed_node
        # поддеревом, выходящим из корня root
        # для это даже не нужен сам root, потому что он остается
        # нужно удалить все ссылки от родителей consumed_node на него
        # если ссылок по какойто полярности у родителя нет
        # то по этому полярности добавляется ссылка в "?"
        # после чего проводится проверка на склейку узлов

        # сперва удаляем узел и все узлы выше его из таблицы, так как их хэши изменятся
        DisjunctiveDiagramsBuilder.DeletingNodesFromTable(consumed_node, diagram, self.nodes_with_changed_hash)

        # затем удаляем поглощенный узел
        DisjunctiveDiagramsBuilder.DeleteNode(self, consumed_node, diagram)

        # затем возвращаем узлы в таблицу, проверяя на склейку
        self.nodes_with_changed_hash = OrderedSet(DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_, self.nodes_with_changed_hash))
        DisjunctiveDiagramsBuilder.GluingNodes(self.nodes_with_changed_hash, diagram)

    def DeleteNode(self, node, diagram):
        # при удалении узла мы удаляем ссылки на него из родителей и детей
        # при этом родителям добавляются ссылки в ?, если нет детей по какойто из полярностей
        # соответственно, если у родителя по обеим полярностям ссылки в вопрос, то мы и его удаляем и тд
        for low_parent in node.low_parents:
            #low_parent.low_childs = [x for x in low_parent.low_childs if x is not node]
            low_parent.low_childs.remove(node)
            DisjunctiveDiagramsBuilder.AddQuestionLink(self,diagram, low_parent)
        for high_parent in node.high_parents:
            #high_parent.high_childs = [x for x in high_parent.high_childs if x is not node]
            high_parent.high_childs.remove(node)
            DisjunctiveDiagramsBuilder.AddQuestionLink(self,diagram, high_parent)
        for low_child in node.low_childs:
            #low_child.low_parents = [x for x in low_child.low_parents if x is not node]
            low_child.low_parents.remove(node)
            #DisjunctiveDiagramsBuilder.AddQuestionLink(self,diagram, low_child)
        for high_child in node.high_childs:
            #high_child.high_parents = [x for x in high_child.high_parents if x is not node]
            high_child.high_parents.remove(node)
            #DisjunctiveDiagramsBuilder.AddQuestionLink(self,diagram, high_child)
        # из табилцы узел уже удалён, но его, возможно, ещё надо удалить из nodes_with_changed_hash
        if node in self.nodes_with_changed_hash:
            # хотя он, по идее, обязательно тут должен быть, так что проверка не особо то и нужна, но пусть будет
            self.nodes_with_changed_hash.remove(node)
        if node.node_type == DiagramNodeType.RootNode:
            diagram.roots_.remove(node)
        del node

    def AddQuestionLink(self,diagram, node):
        if (len(node.low_childs) == 0 and len(node.high_childs) == 0) or \
                (len(node.low_childs) == 0 and diagram.GetQuestionLeaf() in node.high_childs) or \
                (diagram.GetQuestionLeaf() in node.low_childs and len(node.high_childs) == 0):
            DisjunctiveDiagramsBuilder.DeleteNode(self,node,diagram)
        elif len(node.low_childs) == 0:
            node.low_childs.append(diagram.GetQuestionLeaf())
        elif len(node.high_childs) == 0:
            node.high_childs.append(diagram.GetQuestionLeaf())

    # Рекурсивное удаление узлов из таблицы от node наверх
    def DeletingNodesFromTable(node, diagram, deleted_nodes):
        # node.PrintNode('Delete from table:')
        deleted_nodes.add(node)
        if node.hash_key in diagram.table_ and node is not diagram.GetTrueLeaf() and node is not diagram.GetQuestionLeaf():
            del diagram.table_[node.hash_key]
            for parent in set(node.high_parents + node.low_parents):
                DisjunctiveDiagramsBuilder.DeletingNodesFromTable(parent, diagram, deleted_nodes)


    def AddDiagramNode(node:DiagramNode,diagram_):
        if node.hash_key in diagram_.table_:
            it_node:DiagramNode = diagram_.table_[node.hash_key]
            del node
            return it_node
        else:
            node.HashKey()
            diagram_.table_[node.hash_key] = node
            return node


    def EnumerateDiagramNodes(diagram:DisjunctiveDiagram):
        vertex_id = 0
        for node in diagram.table_.values():
            vertex_id += 1
            node.vertex_id = vertex_id


    def LitLessSort(order:list, lits:list):
        abslits = [abs(x) for x in lits]
        litsorder = [x for x in order if x in abslits]
        litsorder.reverse()
        for i in range(len(litsorder)):
            litsorder[i] = (-1) * litsorder[i] if ((-1) * litsorder[i]) in lits else litsorder[i]
        return litsorder

    # Сортировка множества узлов w.r.t. order
    def LitLessSortNodes(order:list,nodes:set):
        nodes = list(nodes)
        sorted_nodes = [node for x in order for node in nodes if node.Value() == x]
        return sorted_nodes

    def LitLessSortNodeswrtOrderAndVertex(order:list, nodes:set):
        nodes = list(nodes)
        sorted_nodes = sorted(nodes, key=lambda x: (order.index(x.Value()), -x.vertex_id))
        return sorted_nodes

    def ClauseLessSort(self,):
        pass

    def __del__(self):
        del self

    def GluingNodes(deleted_nodes, diagram):
        deleted_nodes = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_, deleted_nodes)
        for node in deleted_nodes:
            # node.PrintNode('Before_hash')
            node.HashKey()
            # node.PrintNode('After_hash')
            if node.hash_key in diagram.table_ and diagram.table_[node.hash_key] is not node:
                it_node = diagram.table_[node.hash_key]
                if type(diagram) != DisjunctiveDiagram:
                    diagram.actions_with_links_ += len(node.high_childs) + len(node.low_childs)
                    diagram.actions_with_links_ += len(node.high_parents) + len(node.low_parents)
                    diagram.deleted_nodes_ += 1
                if node is it_node:
                    print('ERROR')
                # print('Glued node',(node.Value(), node),'with node',(it_node.Value(),it_node))
                DisjunctiveDiagramsBuilder.GluingNode(node, it_node)
                del node
            else:
                diagram.table_[node.hash_key] = node

    def GluingNode(node,it_node):
        # заменяем ссылки в родителях
        DisjunctiveDiagramsBuilder.ReplaceParentsLinksToNode(node,it_node)
        # Удаляем ссылки потомков узла на него
        DisjunctiveDiagramsBuilder.DeleteChildsLinksToNode(node)

    def ReplaceParentsLinksToNode(node,it_node):
        for parent in node.high_parents:
            parent.high_childs = [x for x in parent.high_childs if x is not node and x is not it_node]
            parent.high_childs.append(it_node)
            for tmpnode in it_node.high_parents:
                if tmpnode is parent:
                    break
            else:
                #print('add as highparent ', (parent.Value(), parent), 'to node', (it_node.Value(), it_node))
                it_node.high_parents.append(parent)
        for parent in node.low_parents:
            parent.low_childs = [x for x in parent.low_childs if x is not node and x is not it_node]
            parent.low_childs.append(it_node)
            for tmpnode in it_node.low_parents:
                if tmpnode is parent:
                    break
            else:
                it_node.low_parents.append(parent)
                #print('add as lowparent ', (parent.Value(), parent), 'to node', (it_node.Value(), it_node))


    def DeleteChildsLinksToNode(node):
        for child in node.high_childs:
            child.high_parents = [x for x in child.high_parents if x is not node]
        for child in node.low_childs:
            child.low_parents = [x for x in child.low_parents if x is not node]

    def CheckNodesForDelRootGluing(nodes_for_check:OrderedSet, current_node, diagram, deleted_nodes, recur_lvl=0):
        for node in nodes_for_check:
            print('CheckNodesForDelRootGluing Node', node.vertex_id, node.Value())
            DisjunctiveDiagram.PrintCurrentTable(diagram)
            if current_node in node.low_childs:
                DisjunctiveDiagramsBuilder.DeletingNodesFromTable(node, diagram, deleted_nodes)
                node.low_childs.remove(current_node)
            if current_node in node.high_childs:
                DisjunctiveDiagramsBuilder.DeletingNodesFromTable(node, diagram, deleted_nodes)
                node.high_childs.remove(current_node)
            DisjunctiveDiagram.PrintCurrentTable(diagram)
            if (len(node.low_childs) == 0 and len(node.high_childs) == 0) or \
                    (len(node.low_childs) == 0 and diagram.GetQuestionLeaf() in node.high_childs) or \
                    (diagram.GetQuestionLeaf() in node.low_childs and len(node.high_childs) == 0):
                DisjunctiveDiagramsBuilder.DeletingNodesFromTable(node, diagram, deleted_nodes)
                new_nodes_for_check = OrderedSet()
                new_nodes_for_check.update(node.high_parents)
                new_nodes_for_check.update(node.low_parents)
                DisjunctiveDiagramsBuilder.CheckNodesForDelRootGluing(new_nodes_for_check, node, diagram, deleted_nodes, recur_lvl=recur_lvl+1)
                #DisjunctiveDiagramsBuilder.DeleteLinksToNodeInTable(node, diagram)
                deleted_nodes.remove(node)
                del node
            elif len(node.low_childs) == 0:
                node.low_childs.append(diagram.GetQuestionLeaf())
            elif len(node.high_childs) == 0:
                node.high_childs.append(diagram.GetQuestionLeaf())
            # Проверяем ранее удаленные из таблицы узлы на склейку
            DisjunctiveDiagramsBuilder.GluingNodes(deleted_nodes, diagram)

    def DeleteLinksToNodeInTable(delnode,diagram_):
        for node in diagram_.table_.values():
            if delnode in node.low_childs:
                node.low_childs.remove(delnode)
                print('DeleteLinksToNodeInTable deleting',delnode.vertex_id, delnode.Value(),'from low_childs of', node.vertex_id, node.Value())
            if delnode in node.high_childs:
                node.high_childs.remove(delnode)
                print('DeleteLinksToNodeInTable deleting',delnode.vertex_id, delnode.Value(),'from high_childs of', node.vertex_id, node.Value())
            if delnode in node.low_parents:
                node.low_parents.remove(delnode)
                print('DeleteLinksToNodeInTable deleting',delnode.vertex_id, delnode.Value(),'from low_parents of', node.vertex_id, node.Value())
            if delnode in node.high_parents:
                node.high_parents.remove(delnode)
                print('DeleteLinksToNodeInTable deleting',delnode.vertex_id, delnode.Value(),'from high_parents of', node.vertex_id, node.Value())
