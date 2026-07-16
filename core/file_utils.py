import os
import hashlib
import re
from typing import List, Optional

def get_file_hash(filepath: str) -> Optional[str]:
    """
    Calculates the MD5 hash of a file in chunks to minimize memory usage.

    Args:
        filepath (str): The absolute or relative path to the file.

    Returns:
        Optional[str]: The hex digest of the file's MD5 hash, or None if an error occurs.
    """
    if not os.path.exists(filepath):
        return None
        
    hasher = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return None

def get_file_path_parts(filename: str) -> List[str]:
    """
    Splits a filename into logical parts to build a hierarchical tree, 
    stripping technical suffixes and noise words.

    Args:
        filename (str): The name of the file to parse.

    Returns:
        List[str]: A list of logical path parts.
    """
    name = filename.rsplit('.', 1)[0]
    parts = name.split('_')
    
    if len(parts) == 1: 
        return ["Інше"]
        
    path = [parts[0]]
    noise_words = {'old', 'new', 'blink', 'alt', 'intro', 'loop'}
    
    for p in parts[1:]:
        if p.isdigit() or (len(p) <= 2 and len(path) >= 2) or p.lower() in noise_words: 
            break
        # Remove trailing alphanumeric characters commonly used for variations
        clean_p = re.sub(r'[A-Z0-9]+$', '', p)
        path.append(clean_p if clean_p else p)
        
    return path