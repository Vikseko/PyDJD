
# Парсер DIMACS-файла
import ast


def DimacsParser(lines):
    min_var_num = 0
    max_var_num = 0
    lit_count = 0
    lit_count_flag = False
    order = None
    problem = []
    comments = []
    layers = None
    varset = set()
    if len(lines) == 0:
        raise RuntimeError('DimacsParser: Empty file')
    for line in lines:
        if len(line) < 3:
            continue
        elif 'p cnf' in line or 'p dnf' in line:
            vars = int(line.split()[2])
            clauses = int(line.split()[3])
        elif 'c' in line:
            if line[0] == 'c':
                comments.append(line if line[-1] != '\n' else line[:-1])
            if 'literals_count' in line:
                lit_count = int(line.split()[2])
            if 'min_var_num' in line:
                min_var_num = int(line.split()[2])
            if 'max_var_num' in line:
                max_var_num = int(line.split()[2])
            if 'activity_order' in line:
                order = list(reversed(list(map(int, line.split()[2:]))))
            if 'layers' in line:
                layers = ast.literal_eval(line.split(':')[1].strip())
        else:
            if lit_count == 0 and lit_count_flag == False:
                lit_count_flag = True
            clause = list(set(map(int,line.split()[:-1])))
            sat_flag = False
            for lit in clause:
                if -lit in clause:
                    sat_flag = True
                    break
            if not sat_flag:
                for lit in clause:
                    varset.add(abs(lit))
                if len(clause) > 0:
                    problem.append(clause)
                if lit_count_flag:
                    lit_count += len(clause)
    if max_var_num == 0:
        for clause in problem:
            for lit in clause:
                if abs(lit) > max_var_num:
                    max_var_num = abs(lit)
    if min_var_num == 0:
        min_var_num = max_var_num
        for clause in problem:
            for lit in clause:
                if abs(lit) < min_var_num:
                    min_var_num = abs(lit)
            if min_var_num == 1:
                break
    var_count = len(varset)
    return problem, order, comments, var_count, lit_count, min_var_num, max_var_num, layers
