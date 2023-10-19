from Imports import *


def test_bdd(bdd_diagram):
    vars = [x + 1 for x in range(bdd_diagram.variable_count_)]
    vars = sorted(vars, key=lambda x: bdd_diagram.order_.index(abs(x)), reverse=True)
    # inputs = make_inputs(vars)
    nof_inputs = 2**len(vars)
    print('Total possible inputs:', nof_inputs)
    true_paths = []
    false_paths = []
    # print(*inputs, sep='\n')
    counter = 0
    binary_vectors = itertools.product([0, 1], repeat=len(vars))
    # for current_input in inputs:
    while counter < nof_inputs:
        counter += 1
        current_input = make_input(vars, next(binary_vectors))
        # print('Input for check:', current_input)
        result = check_input(current_input, bdd_diagram)
        # print(result)
        if result == 1:
            true_paths.append(current_input)
        elif result == 0:
            false_paths.append(current_input)
        print('Number of checked inputs:', counter, 'true =', len(true_paths), 'false =', len(false_paths), end='\r')
    print()
    for path in true_paths:
        path.sort(key=lambda x: abs(x))
    true_paths.sort()
    for path in false_paths:
        path.sort(key=lambda x: abs(x))
    false_paths.sort()
    return nof_inputs, false_paths, true_paths


def check_input(current_input, bdd_diagram):
    # print('Current input:', current_input)
    root = bdd_diagram.main_root_
    current_node = root
    i = 0
    while i < len(current_input) + 1:
        # current_node.PrintNode('Current node:')
        if current_node.Value() == '?':
            return 0
        elif current_node.Value() == 'true':
            return 1
        elif current_node.Value() == abs(current_input[i]):
            # print('\nCurrent node var:', current_node.Value(), '\nInput variable:', current_input[i])
            if current_input[i] < 0:
                current_node = current_node.low_childs[0]
            else:
                current_node = current_node.high_childs[0]
            i_step = 1
            if current_node.Value() != '?' and current_node.Value() != 'true':
                while abs(current_input[i+i_step]) != current_node.Value():
                    # print(current_input[i+i_step], current_node.Value())
                    i_step += 1
            i += i_step
        else:
            print('ERROR', '\nCurrent node var:', current_node.Value(), '\nInput variable:', current_input[i])
            exit()

def make_inputs(vars):
    binary_vectors = list(itertools.product([0, 1], repeat=len(vars)))
    inputs = []
    for vector in binary_vectors:
        inputs.append(make_input(vars, vector))
    return inputs


def make_input(vars, binary_vector):
    if len(vars) == len(binary_vector):
        current_input = []
        for i in range(len(vars)):
            current_input.append(vars[i] if binary_vector[i] == 1 else -vars[i])
        return current_input
    else:
        print('ERROR len of vars != len of binary vector')
        print('Number of vars:', len(vars), 'Vars:', vars)
        print('Length of binary vector:', len(binary_vector), 'Binary vector:', binary_vector)
        exit()