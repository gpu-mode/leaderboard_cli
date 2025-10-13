"""
Multiplication kernel - Version 1
Generic multiplication operation
"""

def mul_kernel(x, y, output, n):
    """Element-wise multiplication."""
    idx = get_global_id()
    if idx < n:
        output[idx] = x[idx] * y[idx]

