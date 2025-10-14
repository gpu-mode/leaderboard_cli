"""
Float addition kernel - Version 1
Optimized for single-precision floating point operations
"""

def add_float_kernel(x, y, output, n):
    """Element-wise addition of two float arrays."""
    idx = get_global_id()
    if idx < n:
        output[idx] = x[idx] + y[idx]

