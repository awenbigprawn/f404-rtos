import math

def is_greater_or_equal(a, b, epsilon = 1e-15):
    return a > b or math.isclose(a, b, abs_tol=epsilon)

def is_greater(a, b, epsilon = 1e-15):
    return a > b and not math.isclose(a, b, abs_tol=epsilon)

def is_smaller_or_equal(a, b, epsilon = 1e-15):
    return a < b or math.isclose(a, b, abs_tol=epsilon)

def is_smaller(a, b, epsilon = 1e-15):
    return a < b and not math.isclose(a, b, abs_tol=epsilon)

def is_equal(a, b, epsilon = 1e-15):
    return a == b or math.isclose(a, b, abs_tol=epsilon)
