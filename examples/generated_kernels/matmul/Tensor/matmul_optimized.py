"""
Optimized matrix multiplication kernel
Uses tiling and shared memory for better performance
"""

def matmul_tiled(A, B, C, M, N, K):
    """
    Matrix multiplication: C = A @ B
    
    Args:
        A: Input matrix of shape (M, K)
        B: Input matrix of shape (K, N)
        C: Output matrix of shape (M, N)
        M, N, K: Matrix dimensions
    """
    TILE_SIZE = 16
    
    # Thread indices
    tx = get_thread_idx_x()
    ty = get_thread_idx_y()
    
    # Block indices
    bx = get_block_idx_x()
    by = get_block_idx_y()
    
    # Compute row and column indices
    row = by * TILE_SIZE + ty
    col = bx * TILE_SIZE + tx
    
    # Shared memory for tiles
    tile_A = shared_memory((TILE_SIZE, TILE_SIZE))
    tile_B = shared_memory((TILE_SIZE, TILE_SIZE))
    
    # Accumulator
    sum_val = 0.0
    
    # Loop over tiles
    for t in range((K + TILE_SIZE - 1) // TILE_SIZE):
        # Load tiles into shared memory
        if row < M and t * TILE_SIZE + tx < K:
            tile_A[ty][tx] = A[row][t * TILE_SIZE + tx]
        else:
            tile_A[ty][tx] = 0.0
            
        if col < N and t * TILE_SIZE + ty < K:
            tile_B[ty][tx] = B[t * TILE_SIZE + ty][col]
        else:
            tile_B[ty][tx] = 0.0
        
        # Synchronize threads
        sync_threads()
        
        # Compute partial dot product
        for k in range(TILE_SIZE):
            sum_val += tile_A[ty][k] * tile_B[k][tx]
        
        # Synchronize before loading next tile
        sync_threads()
    
    # Write result
    if row < M and col < N:
        C[row][col] = sum_val

