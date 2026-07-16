import logging
from pathlib import Path
from typing import Dict, Set, Optional
from dataclasses import dataclass, field

from .file_utils import get_file_hash

logger = logging.getLogger(__name__)

@dataclass
class AnalysisResult:
    """Data transfer object containing the results of a directory comparison."""
    is_single_mode: bool = False
    files_old_map: Dict[str, Path] = field(default_factory=dict)
    files_new_map: Dict[str, Path] = field(default_factory=dict)
    common_files: Set[str] = field(default_factory=set)
    deleted_files: Set[str] = field(default_factory=set)
    added_files: Set[str] = field(default_factory=set)
    renamed_files: Dict[str, str] = field(default_factory=dict)

class AssetAnalyzer:
    """
    Core engine for comparing two directories to detect added, 
    deleted, common, and renamed files based on names and MD5 hashes.
    """

    @staticmethod
    def analyze(base_path: str, compare_path: Optional[str] = None) -> AnalysisResult:
        """
        Scans and compares files between a base directory and an optional comparison directory.

        Args:
            base_path (str): The path to the base (old) directory.
            compare_path (Optional[str]): The path to the new directory. If None or equal 
                                          to base_path, analysis runs in single mode.

        Returns:
            AnalysisResult: An object containing categorized files and path mappings.
        """
        result = AnalysisResult()
        
        p_old = Path(base_path)
        if not p_old.exists() or not p_old.is_dir():
            logger.error(f"Base path does not exist or is not a directory: {base_path}")
            return result

        # Map base directory files
        result.files_old_map = {f.name: f for f in p_old.rglob('*') if f.is_file()}
        files_old = set(result.files_old_map.keys())

        # Determine mode
        if not compare_path or base_path == compare_path:
            result.is_single_mode = True
            result.files_new_map = result.files_old_map
            result.common_files = files_old
            return result

        p_new = Path(compare_path)
        if not p_new.exists() or not p_new.is_dir():
            logger.error(f"Comparison path does not exist or is not a directory: {compare_path}")
            return result

        # Map comparison directory files
        result.files_new_map = {f.name: f for f in p_new.rglob('*') if f.is_file()}
        files_new = set(result.files_new_map.keys())

        # Find raw differences
        raw_deleted = files_old.difference(files_new)
        raw_added = files_new.difference(files_old)
        result.common_files = files_old.intersection(files_new)

        # Detect renames via MD5 hashing
        hash_del = {}
        for f in raw_deleted:
            h = get_file_hash(str(result.files_old_map[f]))
            if h:
                hash_del[h] = f

        for f in raw_added:
            h = get_file_hash(str(result.files_new_map[f]))
            if h and h in hash_del:
                old_name = hash_del.pop(h)
                result.renamed_files[f] = old_name
            else:
                result.added_files.add(f)

        result.deleted_files = set(hash_del.values())
        return result