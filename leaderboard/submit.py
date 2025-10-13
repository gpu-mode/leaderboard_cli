"""Submission logic for kernel files."""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional
import requests

from .database import SubmissionDB


def submit_single_kernel(
    db: SubmissionDB,
    operation: str,
    dsl: str,
    device: str,
    file_path: str,
    overload: Optional[str] = None,
    endpoint: str = 'http://localhost:8000/submit',
    local_only: bool = True
) -> Dict:
    """Submit a single kernel file.
    
    Args:
        db: Database instance
        operation: Operation type (e.g., 'add', 'mul')
        dsl: DSL type (e.g., 'cutedsl', 'triton')
        device: Device type (e.g., 'A100', 'H100')
        file_path: Path to the kernel file
        overload: Optional overload type
        endpoint: API endpoint URL
        local_only: If True, only store locally without making HTTP request
        
    Returns:
        Dictionary with submission result
    """
    try:
        # Read file content
        with open(file_path, 'r') as f:
            file_content = f.read()
        
        file_name = os.path.basename(file_path)
        
        # Store in local database
        submission_id = db.add_submission(
            operation=operation,
            overload=overload,
            dsl=dsl,
            device=device,
            file_name=file_name,
            file_content=file_content,
            file_path=file_path
        )
        
        # Optionally send to remote endpoint
        if not local_only:
            try:
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
                    timeout=10
                )
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                return {
                    'success': False,
                    'error': f'Failed to submit to remote endpoint: {str(e)}',
                    'submission_id': submission_id,
                    'file_name': file_name
                }
        
        return {
            'success': True,
            'submission_id': submission_id,
            'file_name': file_name,
            'operation': operation
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
                    add_v2.py
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
    
    # Try to determine operation and overload from directory structure
    operation = None
    overload = None
    
    # Get the parent directories
    if len(parts) >= 2:
        # Check if the immediate parent might be an overload type
        parent_name = parts[-2]
        grandparent_name = parts[-3] if len(parts) >= 3 else None
        
        # Common overload types
        overload_types = ['Tensor', 'Float', 'Int', 'Double', 'Half', 'BFloat16']
        
        if parent_name in overload_types and grandparent_name:
            overload = parent_name
            operation = grandparent_name
        else:
            # Parent is likely the operation
            operation = parent_name
    
    # Try to extract operation from filename if not found
    if not operation:
        file_name = path.stem
        # Common pattern: operation_version.py (e.g., add_v1.py)
        match = re.match(r'^([a-zA-Z_]+)(?:_v\d+)?$', file_name)
        if match:
            operation = match.group(1)
    
    return {
        'operation': operation,
        'overload': overload
    }


def submit_directory_kernels(
    db: SubmissionDB,
    dsl: str,
    device: str,
    directory_path: str,
    endpoint: str = 'http://localhost:8000/submit',
    local_only: bool = True
) -> List[Dict]:
    """Submit all kernel files from a directory.
    
    Args:
        db: Database instance
        dsl: DSL type
        device: Device type
        directory_path: Path to directory containing kernel files
        endpoint: API endpoint URL
        local_only: If True, only store locally without making HTTP request
        
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
            # Skip files where we can't determine the operation
            results.append({
                'success': False,
                'error': 'Could not determine operation from path',
                'file_name': file_path.name
            })
            continue
        
        # Submit the kernel
        result = submit_single_kernel(
            db=db,
            operation=operation,
            overload=overload,
            dsl=dsl,
            device=device,
            file_path=str(file_path),
            endpoint=endpoint,
            local_only=local_only
        )
        
        results.append(result)
    
    return results

