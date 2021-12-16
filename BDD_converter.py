from Pathfinder import *
import pysat
from pysat.solvers import MapleChrono
from pysat.formula import CNF

from Types import DiagramNode


class BDDiagram:
    def __init__(self,diagram:DisjunctiveDiagram):
        self.variable_count_ = diagram.variable_count_
        self.true_path_count_ = diagram.true_path_count_
        self.question_path_count_ = diagram.question_path_count_
        self.false_path_count_ = diagram.false_path_count_
        self.max_path_depth_ = diagram.max_path_depth_
        self.duplicate_reduced_ = diagram.duplicate_reduced_
        self.vertex_reduced_ = diagram.vertex_reduced_
        self.min_var_num_ = diagram.min_var_num_
        self.max_var_num_ = diagram.max_var_num_
        self.root_join_cnt_ = diagram.root_join_cnt_
        self.problem_type_ = diagram.problem_type_
        self.order_ = copy.copy(diagram.order_)
        self.table_ = copy.copy(diagram.table_)
        self.roots_ = copy.copy(diagram.roots_)
        self.main_root_ = None
        self.var_set_ = copy.copy(diagram.var_set_)
        BDD_convert(self)


    # Возвращает таблицу
    def GetTable(self):
        return self.table_

    # Возвращает множество корней
    def GetRoots(self):
        return self.roots_

    # Возращает тип исходной формулы: кнф, днф, конфликтная база
    def GetProblemType(self):
        return self.problem_type_

    # Возвращает число переменных
    def VariableCount(self):
        return len(self.var_set_)

    # Возвращает переменную с наименьшим номером
    def MinVarId(self):
        return self.var_set_[0] if len(self.var_set_) > 0 else 0

    # Возвращает переменную с наибольшим номером
    def MaxVarId(self):
        return self.var_set_[-1] if len(self.var_set_) > 0 else 0

    # Возвращает число вершин в диаграмме
    def VertexCount(self):
        return len(self.table_)

    # Возвращает число путей в 1
    def TruePathCount(self):
        return self.true_path_count_

    # Возвращает число путей в ?
    def QuestionPathCount(self):
        return self.question_path_count_

    # Возвращает число путей в 0
    def FalsePathCount(self):
        return self.false_path_count_

    # Возвращает максимальную длину пути
    def MaxPathDepth(self):
        return self.max_path_depth_

    # Возвращает терминальный узел ?
    def GetQuestionLeaf(self):
        return self.table_[hash(tuple(['?']+[]+[]))]

    # Возвращает терминальный узел 1
    def GetTrueLeaf(self):
        return self.table_[hash(tuple(['true']+[]+[]))]

    # Возвращается число удаленных узлов изза дупликации потомков (когда потомки совпадают по ребрам разной полярности)
    def DuplicateReducedCount(self):
        return self.duplicate_reduced_

    def VertexReducedCount(self):
        return self.vertex_reduced_

    def RootJoinCount(self):
        return self.root_join_cnt_

    # Возвращает размер диаграммы в байтах
    def DiagramSize(self):
        size = 0
        for node in self.table_:
            size += node.Size()
        return size

    def __del__(self):
        for node in self.table_:
            del node


def BDD_convert(diagram):
    # сперва надо свести корни к одному. для этого берём корень с наименьшим порядковым номером (относительно order)
    # затем добавляем ему ссылки на каждый другой корень причем и в high_childs и в low_childs
    roots_ = DisjunctiveDiagramsBuilder.LitLessSortNodes(diagram.order_, diagram.roots_)
    main_root = roots_[-1]
    for root in roots_[:-1]:
        connect_roots(main_root, root)
    diagram.main_root_ = main_root
    # Теперь вся диаграмма выходит из одного корня.

    # начинаем рекурсивно уводить связи вниз.
    """ алгоритм:
    1. идем от терминальной вершины наверх, ищем узел А, у которого небинарность
    2. при нахождении берём небинарные ветки (которые лишние), к примеру из узла А идут три связи по минусу, 
    одна по плюсу. Удаляем связи лишних ветвей с узлом А. Добавляем эти связи первому по order ребенку А по минусу (в
     данном примере). Причем добавляем их сразу и по плюсу и по минусу этому ребенку.
    3. Рекурсивно проверяем вниз, заодно постоянно проверяя на склейку.
    условно рано или поздно будет момент, когда все свзяи из узла будут идти в терминальные вершины. тогда начинаем
    проверять на склейку и на повторы детей по разным полярностям: если из узла А дети +Б1(х1) и -Б1(х1) с детьми
    , то узел А надо удалить, а +Б1 и -Б1 перенаправить родителям А.
    4. повторяем это пока небинарности больше не будет найдено.
    """



def connect_roots(main_root, root):
    if root not in main_root.high_childs:
        main_root.high_childs.append(root)
    if root not in main_root.low_childs:
        main_root.low_childs.append(root)
    root.node_type = DiagramNodeType.InternalNode
