def DimacsParser(lines,problem,order):
    min_var_num = 0
    max_var_num = 0
    lit_count = 0
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
