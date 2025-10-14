"""
Tensor addition kernel - Version 2
Vectorized implementation for better memory throughput
"""

def add_kernel_vectorized(x, y, output, n):
    """Vectorized element-wise addition of two tensors."""
    idx = get_global_id()
    vec_idx = idx * 4
    
    if vec_idx + 3 < n:
        # Process 4 elements at once
        output[vec_idx] = x[vec_idx] + y[vec_idx]
        output[vec_idx + 1] = x[vec_idx + 1] + y[vec_idx + 1]
        output[vec_idx + 2] = x[vec_idx + 2] + y[vec_idx + 2]
        output[vec_idx + 3] = x[vec_idx + 3] + y[vec_idx + 3]

