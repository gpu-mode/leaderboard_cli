"""
Tensor addition kernel - Version 1
Optimized for A100 GPUs
"""

def add_kernel(x, y, output, n):
    """Element-wise addition of two tensors."""
    idx = get_global_id()
    if idx < n:
        output[idx] = x[idx] + y[idx]

