"""
Graph-Based Dependency Conflict Detection
"""

from typing import Dict, List, Any, Set, Optional, Tuple


class ConflictDetector:
    """
    Detects dependency conflicts using graph-based analysis
    """
    
    def __init__(self):
        # Known dependency relationships
        self.dependency_graph = self._build_dependency_graph()
        
    def _build_dependency_graph(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Build a simplified dependency graph
        In production, this would be loaded from PyPI metadata
        """
        return {
            'numpy': {
                '1.19': ['python>=3.6,<3.9'],
                '1.21': ['python>=3.7,<3.11'],
                '1.24': ['python>=3.8,<3.12'],
            },
            'pandas': {
                '1.2': ['python>=3.7', 'numpy>=1.16.5'],
                '1.5': ['python>=3.8', 'numpy>=1.20.3'],
                '2.0': ['python>=3.8', 'numpy>=1.20.3'],
            },
            'scipy': {
                '1.7': ['python>=3.7', 'numpy>=1.16.5'],
                '1.10': ['python>=3.8', 'numpy>=1.19.5'],
            },
            'sklearn': {
                '0.24': ['python>=3.6', 'numpy>=1.13.3', 'scipy>=0.19.1'],
                '1.0': ['python>=3.7', 'numpy>=1.14.6', 'scipy>=1.1.0'],
                '1.2': ['python>=3.8', 'numpy>=1.17.3', 'scipy>=1.3.2'],
            },
            'matplotlib': {
                '3.4': ['python>=3.7', 'numpy>=1.16'],
                '3.7': ['python>=3.8', 'numpy>=1.19'],
            },
            'tensorflow': {
                '2.6': ['python>=3.6,<3.10', 'numpy>=1.19.2'],
                '2.10': ['python>=3.7,<3.11', 'numpy>=1.20'],
                '2.12': ['python>=3.8,<3.12', 'numpy>=1.22'],
            },
            'torch': {
                '1.9': ['python>=3.6,<3.10', 'numpy'],
                '2.0': ['python>=3.8,<3.12', 'numpy'],
            }
        }
    
    def detect_conflicts(
        self,
        packages: List[str],
        python_version: str
    ) -> List[Dict[str, Any]]:
        """
        Detect conflicts in package list
        
        Args:
            packages: List of package names
            python_version: Target Python version
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        # Check Python version compatibility for each package
        for package in packages:
            if package in self.dependency_graph:
                # Get latest version's requirements
                versions = list(self.dependency_graph[package].keys())
                latest_version = versions[-1]  # Simplified: assume sorted
                requirements = self.dependency_graph[package][latest_version]
                
                # Check Python version constraint
                for req in requirements:
                    if req.startswith('python'):
                        if not self._check_python_constraint(req, python_version):
                            conflicts.append({
                                'type': 'python_version',
                                'package': package,
                                'version': latest_version,
                                'constraint': req,
                                'current_python': python_version,
                                'description': f"{package} {latest_version} requires {req}, but Python {python_version} specified"
                            })
        
        # Check inter-package conflicts
        for i, pkg1 in enumerate(packages):
            for pkg2 in packages[i+1:]:
                conflict = self._check_package_conflict(pkg1, pkg2, python_version)
                if conflict:
                    conflicts.append(conflict)
        
        return conflicts
    
    def _check_python_constraint(self, constraint: str, python_version: str) -> bool:
        """
        Check if Python version satisfies constraint
        
        Args:
            constraint: e.g., "python>=3.7,<3.11"
            python_version: e.g., "3.8"
            
        Returns:
            True if constraint is satisfied
        """
        try:
            # Parse Python version
            py_major, py_minor = map(int, python_version.split('.')[:2])
            py_ver = (py_major, py_minor)
            
            # Parse constraint
            constraint = constraint.replace('python', '').replace('=', '').replace(' ', '')
            
            # Handle multiple constraints (e.g., ">=3.7,<3.11")
            parts = constraint.split(',')
            
            for part in parts:
                if '>=' in part:
                    min_ver = part.replace('>=', '')
                    min_major, min_minor = map(int, min_ver.split('.')[:2])
                    if py_ver < (min_major, min_minor):
                        return False
                        
                elif '>' in part:
                    min_ver = part.replace('>', '')
                    min_major, min_minor = map(int, min_ver.split('.')[:2])
                    if py_ver <= (min_major, min_minor):
                        return False
                        
                elif '<=' in part:
                    max_ver = part.replace('<=', '')
                    max_major, max_minor = map(int, max_ver.split('.')[:2])
                    if py_ver > (max_major, max_minor):
                        return False
                        
                elif '<' in part:
                    max_ver = part.replace('<', '')
                    max_major, max_minor = map(int, max_ver.split('.')[:2])
                    if py_ver >= (max_major, max_minor):
                        return False
            
            return True
            
        except Exception:
            return True  # If parsing fails, assume compatible
    
    def _check_package_conflict(
        self,
        pkg1: str,
        pkg2: str,
        python_version: str
    ) -> Optional[Dict[str, Any]]:
        """
        Check if two packages have conflicting requirements
        """
        # Simplified conflict detection
        # In production, this would check actual dependency constraints
        
        # Known conflicts
        known_conflicts = {
            ('tensorflow', 'torch'): "TensorFlow and PyTorch may conflict on CUDA versions",
        }
        
        pair = tuple(sorted([pkg1, pkg2]))
        if pair in known_conflicts:
            return {
                'type': 'package_conflict',
                'packages': list(pair),
                'description': known_conflicts[pair]
            }
        
        return None
    
    def suggest_resolution(self, conflicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Suggest resolutions for detected conflicts
        
        Args:
            conflicts: List of conflicts from detect_conflicts()
            
        Returns:
            List of suggested resolutions
        """
        suggestions = []
        
        for conflict in conflicts:
            if conflict['type'] == 'python_version':
                # Suggest compatible Python version
                constraint = conflict['constraint']
                
                # Parse constraint to suggest version
                if '>=' in constraint and '<' in constraint:
                    # Extract range
                    parts = constraint.replace('python', '').split(',')
                    min_ver = parts[0].replace('>=', '').strip()
                    max_ver = parts[1].replace('<', '').strip()
                    
                    # Suggest middle version
                    try:
                        min_major, min_minor = map(int, min_ver.split('.')[:2])
                        max_major, max_minor = map(int, max_ver.split('.')[:2])
                        
                        # Suggest one below max
                        suggested = f"{max_major}.{max_minor - 1}"
                        
                        suggestions.append({
                            'conflict': conflict,
                            'suggestion': f"Use Python {suggested}",
                            'python_version': suggested
                        })
                    except Exception:
                        pass
            
            elif conflict['type'] == 'package_conflict':
                suggestions.append({
                    'conflict': conflict,
                    'suggestion': "Consider using only one of these packages, or check for compatible versions"
                })
        
        return suggestions
