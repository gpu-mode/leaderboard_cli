"""Submission logic for kernel files."""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional
import requests


def submit_single_kernel(
    operation: str,
    dsl: str,
    device: str,
    file_path: str,
    token: str,
    overload: Optional[str] = None,
    endpoint: str = 'http://localhost:8000/api/submit'
) -> Dict:
    """Submit a single kernel file to the server.
    
    Args:
        operation: Operation type (e.g., 'add', 'mul')
        dsl: DSL type (e.g., 'cutedsl', 'triton')
        device: Device type (e.g., 'A100', 'H100')
        file_path: Path to the kernel file
        overload: Optional overload type
        endpoint: API endpoint URL
        
    Returns:
        Dictionary with submission result
    """
    try:
        # Read file content
        with open(file_path, 'r') as f:
            file_content = f.read()
        
        file_name = os.path.basename(file_path)
        
        # Send to server with authentication
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            endpoint,
            json={
                'operation': operation,
                'overload': overload,
                'dsl': dsl,
                'device': device,
                'file_name': file_name,
                'file_content': file_content
            },
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        result = response.json()
        
        return {
            'success': True,
            'submission_id': result['id'],
            'file_name': file_name,
            'operation': operation
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Failed to submit to server: {str(e)}',
            'file_name': os.path.basename(file_path) if file_path else 'unknown'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'file_name': os.path.basename(file_path) if file_path else 'unknown'
        }


def parse_kernel_info_from_path(file_path: str) -> Dict[str, Optional[str]]:
    """Parse operation and overload information from file path.
    
    Expected directory structure:
        generated_kernels/
            add/
                Tensor/
                    add_v1.py
                Float/
                    add_v1.py
            mul/
                mul_v1.py
    
    Args:
        file_path: Path to the kernel file
        
    Returns:
        Dictionary with 'operation' and 'overload' keys
    """
    path = Path(file_path)
    parts = path.parts
    
    operation = None
    overload = None
    
    if len(parts) >= 2:
        parent_name = parts[-2]
        grandparent_name = parts[-3] if len(parts) >= 3 else None
        
        # Common overload types
        overload_types = ['Tensor', 'Float', 'Int', 'Double', 'Half', 'BFloat16']
        
        if parent_name in overload_types and grandparent_name:
            overload = parent_name
            operation = grandparent_name
        else:
            operation = parent_name
    
    # Try to extract operation from filename if not found
    if not operation:
        file_name = path.stem
        match = re.match(r'^([a-zA-Z_]+)(?:_v\d+)?$', file_name)
        if match:
            operation = match.group(1)
    
    return {
        'operation': operation,
        'overload': overload
    }


def submit_directory_kernels(
    dsl: str,
    device: str,
    directory_path: str,
    token: str,
    endpoint: str = 'http://localhost:8000/api/submit'
) -> List[Dict]:
    """Submit all kernel files from a directory to the server.
    
    Args:
        dsl: DSL type
        device: Device type
        directory_path: Path to directory containing kernel files
        endpoint: API endpoint URL
        
    Returns:
        List of submission result dictionaries
    """
    results = []
    directory = Path(directory_path)
    
    # Find all Python files in the directory (recursively)
    kernel_files = list(directory.rglob('*.py'))
    
    # Also support other common kernel file extensions
    for ext in ['*.cu', '*.cpp', '*.c', '*.cuh', '*.h']:
        kernel_files.extend(directory.rglob(ext))
    
    for file_path in kernel_files:
        # Parse operation and overload from path
        info = parse_kernel_info_from_path(str(file_path))
        operation = info['operation']
        overload = info['overload']
        
        if not operation:
            results.append({
                'success': False,
                'error': 'Could not determine operation from path',
                'file_name': file_path.name
            })
            continue
        
        # Submit the kernel
        result = submit_single_kernel(
            operation=operation,
            overload=overload,
            dsl=dsl,
            device=device,
            file_path=str(file_path),
            token=token,
            endpoint=endpoint
        )
        
        results.append(result)
    
    return results
