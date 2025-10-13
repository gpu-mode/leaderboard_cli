"""
Example kernel implementation for tensor addition using CuteDSL.
This is a sample implementation for demonstration purposes.
"""

def add_tensor(a, b, output):
    """
    Add two tensors element-wise.
    
    Args:
        a: Input tensor A
        b: Input tensor B
        output: Output tensor for storing A + B
    """
    # CuteDSL implementation
    blockIdx_x = get_block_idx_x()
    threadIdx_x = get_thread_idx_x()
    
    idx = blockIdx_x * blockDim_x + threadIdx_x
    
    if idx < a.size:
        output[idx] = a[idx] + b[idx]
    
    return output


def kernel_config():
    """Return kernel configuration parameters."""
    return {
        'block_size': 256,
        'grid_size': 'auto',
        'shared_memory': 0
    }

