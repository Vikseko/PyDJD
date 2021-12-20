
# Парсер DIMACS-файла
def DimacsParser(lines):
    min_var_num = 0
    max_var_num = 0
    lit_count = 0
    lit_count_flag = False
    order = None
    problem = []
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
            if 'literals_count' in line:
                lit_count = int(line.split()[2])
            if 'min_var_num' in line:
                min_var_num = int(line.split()[2])
            if 'max_var_num' in line:
                max_var_num = int(line.split()[2])
            if 'activity_order' in line:
                order = reversed(list(map(int,line.split()[2:])))
        else:
            if lit_count == 0 and lit_count_flag == False:
                lit_count_flag = True
            clause = list(map(int,line.split()[:-1]))
            for lit in clause:
                varset.add(abs(lit))
            problem.append(clause)
            if lit_count_flag == True:
                lit_count += len(clause)
    if min_var_num == 0:
        for clause in problem:
            for lit in clause:
                if abs(lit) < min_var_num or abs(lit) == 1:
                    min_var_num = abs(lit)
    if max_var_num == 0:
        for clause in problem:
            for lit in clause:
                if abs(lit) > max_var_num:
                    max_var_num = abs(lit)
    var_count = len(varset)
    return problem, order, var_count, lit_count, min_var_num, max_var_num
