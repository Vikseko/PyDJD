# Парсер DIMACS-файла
def DimacsParser(lines):
    min_var_num = 0
    max_var_num = 0
    lit_count = 0
    order = None
    problem = []
    if len(lines) == 0:
        print('DimacsParser: Empty file')
        return 0
    for line in lines:
        if len(line) == 0:
                continue
        elif 'p cnf' or 'p dnf' in line:
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
                order = list(map(int,line.split()[2:]))
        else:
            clause = list(map(int,line.split()[:-1]))
            problem.append(clause)
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
        return problem, order, lit_count, min_var_num, max_var_num
