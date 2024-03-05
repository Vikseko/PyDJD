"""
Test CNFs:
test1.cnf
test2.cnf
test3.cnf
GeffeLearntsClauses_1.cnf
md4_48_lambda_1_simplified_up_1.cnf
BubbleVsPancakeSort_6_4.cnf

Tests_tmp:
BubbleVsPancakeSort_7_5
BubbleVsPancakeSort_7_6
BubbleVsPancakeSort_8_4
BubbleVsPancakeSort_8_5
PancakeVsInsertSort_6_8
PancakeVsInsertSort_7_5
PancakeVsInsertSort_8_4
PancakeVsInsertSort_8_5
PancakeVsSelectionSort_6_6
PancakeVsSelectionSort_7_4
PancakeVsSelectionSort_7_5
PancakeVsSelectionSort_7_6
php_3holes.cnf
php_5holes.cnf
php_10holes.cnf
"""

import argparse
#Parser
def createParser ():
    parser = argparse.ArgumentParser()
    parser.add_argument ('-f', '--file', nargs='?', type=str, default='Tests/GeffeLearntsClauses_1.cnf')
    parser.add_argument ('-o', '--order', nargs='?', type=str, default='frequency', help='{activity, frequency, '
                                                                                         'revfrequency, direct,'
                                                                                         'layers} Order '
                                                                                         'of variables for '
                                                                                         'building diagrams')
    parser.add_argument ('-s', '--source', nargs='?', type=str, default='cnf')
    parser.add_argument('-rt', '--runtests', nargs='?', type=bool, default=False)
    parser.add_argument('-ss', '--show_stats', nargs='?', type=bool, default=False)
    parser.add_argument('-sv', '--show_ver', nargs='?', type=bool, default=False)
    parser.add_argument ('-so', '--show_options', nargs='?', type=str, default='True')
    parser.add_argument('-bdd', '--bdd_convert', nargs='?', type=str, default='False')
    parser.add_argument('-tbdd', '--test_bdd_convert', nargs='?', type=str, default='False')
    parser.add_argument('-sc', '--separate_construction', nargs='?', type=str, default='False')
    parser.add_argument ('-rp', '--redirpaths', nargs='?', type=str, default='False')
    parser.add_argument('-prep', '--djd_prep', nargs='?', type=str, default='False')
    parser.add_argument('-lv', '--lockvars', nargs='?', type=str, default='False')
    parser.add_argument('-al', '--analyze_log', nargs='?', type=str, default='')
    parser.add_argument('-avl', '--analyze_var_limit', nargs='?', type=int, default=20)
    parser.add_argument('-avf', '--analyze_var_fraction', nargs='?', type=float, default=0.5)
    parser.add_argument('-np', '--numproc', nargs='?', type=int, default=1)
    parser.add_argument('-pbi', '--pbintervals', nargs='?', type=int, default=1, help='Number of PB intervals.')
    parser.add_argument('-ao', '--applyonly', nargs='?', type=int, default=0, help='Apply only mode')
    parser.add_argument('-pbio', '--pbiorder', nargs='?', type=str, default='direct', help='Order of intervals to apply: {direct, reversed, random}')
    parser.add_argument('-ep', '--ep_flag', nargs='?', type=int, default=0, help='Existential projection mode')
    parser.add_argument('-epo', '--ep_order', nargs='?', type=str, default='direct', help='Order of vars for existential projection: {direct, reversed, random}.')
    parser.add_argument('-sdjdp', '--sep_djd_prep', nargs='?', type=int, default=0, help='Separate DJD-preprocessing mode (1 -- biggest DJD, 2 -- all DJDs, 3 -- all DJDs, but hard paths separately)')
    parser.add_argument('-preptl', '--djd_prep_time_limit', nargs='?', type=int, default=0,
                        help='Time limit (in seconds) for single path in DJD-preprocessing (0 -- no time limit).')
    parser.add_argument('-prepbm', '--prepbinmode', nargs='?', type=int, default=0,
                        help='Binarization mode for separate preprocessing')
    parser.add_argument('-bddms', '--bdd_max_size', nargs='?', type=int, default=1000000)
    parser.add_argument('-bddmp', '--bdd_max_paths', nargs='?', type=int, default=10000)
    parser.add_argument('-htfn', '--hardtasksfilename', nargs='?', type=str, default='res_UCfinder_bs10_withcorrshortlearnts_kissat_500s_lec_mult_CvK_12x12_bds10_iter0.log')

    return parser


