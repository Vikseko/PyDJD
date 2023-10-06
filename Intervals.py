from Imports import *


######################################################################################################
##----------------------------------------UTILITY FUNCTIONS-----------------------------------------##
######################################################################################################

def str2bits(s):
    return [{'1': True, '0': False}[c] for c in s]

def bits2str(bits):
    return ''.join(str(int(b)) for b in bits)

def num2str(x, n):
    # return bin(x)[2:].rjust(n, '0')
    return f"{x:0{n}b}"

def num2bits(x, n):
    return str2bits(num2str(x, n))

def bits2num(bits):
    return int(bits2str(bits), 2)

######################################################################################################
##----------------------------------------ENCODING FUNCTIONS----------------------------------------##
######################################################################################################

def _encode_geq(x, a):
    assert len(x) == len(a)

    if len(x) == 0:
        return []

    clauses = []
    assert isinstance(a[0], bool)
    if a[0]:
        clauses.append([x[0]])
        clauses.extend(_encode_geq(x[1:], a[1:]))
    else:
        # Append (x=1) to all sub-clauses:
        for clause in _encode_geq(x[1:], a[1:]):
            clauses.append([x[0]] + clause)
    return clauses


def _encode_leq(x, b):
    assert len(x) == len(b)

    if len(x) == 0:
        return []

    clauses = []
    assert isinstance(b[0], bool)
    if not b[0]:
        clauses.append([-x[0]])
        clauses.extend(_encode_leq(x[1:], b[1:]))
    else:
        # Append (x=0) to all sub-clauses:
        for clause in _encode_leq(x[1:], b[1:]):
            clauses.append([-x[0]] + clause)
    return clauses


def _encode_both(x, a, b):
    assert len(x) == len(a)
    assert len(x) == len(b)

    if len(x) == 0:
        return []

    clauses = []
    assert isinstance(a[0], bool)
    assert isinstance(b[0], bool)
    if a[0]:
        assert b[0]
        clauses.append([x[0]])
        clauses.extend(_encode_both(x[1:], a[1:], b[1:]))
    elif not b[0]:
        assert not a[0]
        clauses.append([-x[0]])
        clauses.extend(_encode_both(x[1:], a[1:], b[1:]))
    else:
        assert not a[0]
        assert b[0]
        # Append (x=1) to all sub-clauses:
        for clause in _encode_geq(x[1:], a[1:]):
            clauses.append([x[0]] + clause)
        # Append (x=0) to all sub-clauses:
        for clause in _encode_leq(x[1:], b[1:]):
            clauses.append([-x[0]] + clause)
    return clauses


######################################################################################################
##----------------------------------------HIGH-LEVEL WRAPPER----------------------------------------##
######################################################################################################

def encode_rel(lits, mode, bound):
    """
    Returns a list of clauses encoding the fact `x _rel_ bound`, where:
    - `rel` is either `>=` (`mode='geq'`) or `<=` (`mode='leq'`),
    - `lits` are the bits of `x` (note: `lits[0]` is MSB).
    """

    n = len(lits)
    #print(f"=== Encoding '{mode}' for n = {n}, bound = {bound}")
    if mode == "geq":
        assert 0 <= bound < 2**n
        a = num2bits(bound, n)
        return _encode_geq(lits, a)
    elif mode == "leq":
        assert 0 <= bound < 2**n
        a = num2bits(bound, n)
        return _encode_leq(lits, a)
    elif mode == "both":
        if isinstance(bound, tuple):
            (min_bound, max_bound) = bound
            assert 0 <= min_bound < 2**n
            assert 0 <= max_bound < 2**n
        else:
            assert 0 <= bound < 2**n
            min_bound = max_bound = bound
        a = num2bits(min_bound, n)
        b = num2bits(max_bound, n)
        return _encode_both(lits, a, b)

######################################################################################################
##-----------------------------------------------MAIN-----------------------------------------------##
######################################################################################################
