"""
Test CNFs:
test1.cnf
test2.cnf
test3.cnf
GeffeLearntsClauses_1.cnf
md4_48_lambda_1_simplified_up_0.cnf
PancakeVsSelectionSort_6_6.cnf
PancakeVsSelectionSort_6_7.cnf
PancakeVsSelectionSort_7_4.cnf
PancakeVsSelectionSort_7_5.cnf
PancakeVsSelectionSort_7_6.cnf
"""

import argparse
#Parser
def createParser ():
    parser = argparse.ArgumentParser()
    parser.add_argument ('-f', '--file', nargs='?', type=str, default='Tests_tmp/PancakeVsSelectionSort_6_6.cnf')
    parser.add_argument ('-o', '--order', nargs='?', type=str, default='frequency')
    parser.add_argument ('-s', '--source', nargs='?', type=str, default='cnf')
    parser.add_argument('-rt', '--runtests', nargs='?', type=bool, default=False)
    parser.add_argument('-ss', '--show_stats', nargs='?', type=bool, default=False)
    parser.add_argument('-sv', '--show_ver', nargs='?', type=bool, default=False)
    parser.add_argument ('-so', '--show_options', nargs='?', type=bool, default=False)
    parser.add_argument('-bdd', '--bdd_convert', nargs='?', type=bool, default=False)
    parser.add_argument ('-rp', '--redirpaths', nargs='?', type=bool, default=True)
    parser.add_argument('-lv', '--lockvars', nargs='?', type=bool, default=False)
    parser.add_argument('-al', '--analyze_log', nargs='?', type=str, default='')
    parser.add_argument('-avl', '--analyze_var_limit', nargs='?', type=int, default=20)
    parser.add_argument('-avf', '--analyze_var_fraction', nargs='?', type=float, default=0.5)
    return parser

