from collections import defaultdict
from typing import Tuple, List, Dict

class TreeNode:
    """
    Represents a hierarchical node for storing the state of files 
    (deleted, added, common, renamed) within a tree structure.
    """

    def __init__(self):
        """Initializes an empty tree node with categorised file lists."""
        self.deleted: List[str] = []
        self.added: List[str] = []
        self.common: List[str] = []
        self.renamed: List[Tuple[str, str]] = []  # List of (new_name, old_name)
        self.children: Dict[str, 'TreeNode'] = defaultdict(TreeNode)

    def count_recursive(self) -> Tuple[int, int, int, int]:
        """
        Recursively counts the number of files in each status for this node 
        and all its descendants.

        Returns:
            Tuple[int, int, int, int]: A tuple containing counts of 
            (deleted, added, common, renamed) files.
        """
        d = len(self.deleted)
        a = len(self.added)
        c = len(self.common)
        r = len(self.renamed)
        
        for child in self.children.values():
            cd, ca, cc, cr = child.count_recursive()
            d += cd
            a += ca
            c += cc
            r += cr
            
        return d, a, c, r